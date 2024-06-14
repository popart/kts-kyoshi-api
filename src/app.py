from datetime import datetime, timedelta
import json
import logging
import os
import sys
import uuid

import flask
import flask_cors
import fsrs
import sqlalchemy
from werkzeug.wrappers.response import Response

from prompts.prompt_flash_cards import get_prompt_flash_cards
from clients.chat.openai_chat_client import OpenAIChatClient
from clients.chat.fake_chat_client import FakeChatClient
from data_types import chat_types, chat_response_types, flash_card_types
from handlers import chat_handler, user_handler, flash_card_handler

from google.oauth2 import id_token
from google.auth.transport import requests


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# log to stdout
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# setup from env (move this to a file)
SESSION_SECRET_KEY = os.environ["SESSION_SECRET_KEY"]
GOOGLE_OAUTH_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
ENV = os.getenv("ENV", "local")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")

# setup flask app
app = flask.Flask(__name__)
app.secret_key = SESSION_SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 4 * 1000 * 1000  # 4 MB

flask_cors.CORS(app, supports_credentials=True)

# init app (ghetto DI)
if ENV != "test":
    CHAT_CLIENT = OpenAIChatClient()
else:
    CHAT_CLIENT = FakeChatClient(response_type=os.getenv("CHAT_TYPE", "CHAT"))

if ENV == "gcp":
    unix_socket_path = os.environ["INSTANCE_UNIX_SOCKET"]
    db_url = sqlalchemy.engine.url.URL.create(
        drivername="postgresql+psycopg",
        username="postgres",
        password=DB_PASSWORD,
        database="kyoshi",
        query={"host": unix_socket_path},
    )
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_DOMAIN"] = "goginko.com"
else:
    db_url = sqlalchemy.engine.url.URL.create(
        drivername="postgresql+psycopg",
        username="postgres",
        password=DB_PASSWORD,
        host="localhost",
        port=5432,
        database="kyoshi",
    )
DB_ENGINE = sqlalchemy.create_engine(db_url)

PROMPT_FLASHCARDS = get_prompt_flash_cards(CHAT_CLIENT)
CHATS: dict[str, list[chat_types.ChatMessage]] = {}


CHAT_LOOKBACK = -3


@app.route("/", methods=["GET"])
def homepage():
    return "Ack! What are you doing back here?!"


@app.route("/login", methods=["POST"])
def login():
    data = flask.request.json
    token = data.get("token") if data else None

    # Verify the token here using Google's library or any other method
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_OAUTH_CLIENT_ID
        )
        openid_sub = idinfo["sub"]
        openid_email = idinfo["email"]

        # create a session! this will create a session token

        if not user_handler.user_exists(DB_ENGINE, openid_sub):
            user_handler.create_user(DB_ENGINE, openid_sub, openid_email)
        flask.session["openid_sub"] = openid_sub

        return (
            flask.jsonify(
                {
                    "message": "Token is valid",
                }
            ),
            200,
        )

    except ValueError as e:
        return flask.jsonify({"message": str(e)}), 400


@app.route("/check_login", methods=["GET", "POST"])
def check_login():
    is_logged_in = flask.session.get("openid_sub") is not None
    return flask.jsonify({"loggedIn": is_logged_in}), 200


@app.route("/logout", methods=["POST"])
def logout():
    flask.session.clear()  # This clears the entire session
    return flask.jsonify({"message": "Logged out successfully"}), 200


@app.route("/chat", defaults={"chat_id": None}, methods=["GET", "POST", "DELETE"])
@app.route("/chat/<chat_id>", methods=["GET", "POST", "DELETE"])
def chat(chat_id):
    """Returns a list of chats"""
    current_user_sub = flask.session.get("openid_sub")
    if not current_user_sub:
        flask.abort(Response("Please log in", 401))

    user_id = user_handler.get_user_id(DB_ENGINE, current_user_sub)
    assert user_id is not None

    response = {}

    # GET returns all chats
    if flask.request.method == "GET":
        response = chat_handler.get_chats(engine=DB_ENGINE, user_id=user_id)

    # DELETE deletes a single chat
    elif flask.request.method == "DELETE":
        assert chat_id is not None
        try:
            chat_id = uuid.UUID(chat_id)
        except ValueError:
            flask.abort(Response("Not a valid chat id", 404))
        chat_handler.delete_chat(engine=DB_ENGINE, user_id=user_id, chat_id=chat_id)
        response = {"status": "SUCCESS"}

    # POST creates a new chat
    else:
        if chat_id is not None:
            try:
                chat_id = uuid.UUID(chat_id)
            except ValueError:
                flask.abort(Response("Not a valid chat id", 404))

            data = flask.request.json
            chat_name = data.get("chat_name") if data else None

            chat_handler.update_chat(
                engine=DB_ENGINE, user_id=user_id, chat_id=chat_id, chat_name=chat_name
            )
        else:
            chat_handler.create_chat(engine=DB_ENGINE, user_id=user_id)
        response = {"status": "SUCCESS"}

    return flask.jsonify(response), 200


@app.route("/chat_message/<chat_id>", methods=["GET", "POST"])
def chat_message(chat_id):
    current_user_sub = flask.session.get("openid_sub")
    if not current_user_sub:
        flask.abort(Response("Please log in", 401))

    try:
        chat_id = uuid.UUID(chat_id)
    except ValueError:
        flask.abort(Response("Not a valid chat id", 404))

    user_id = user_handler.get_user_id(DB_ENGINE, current_user_sub)
    assert user_id is not None

    # TODO: assert chat_id matches user_id

    # chat_message_data: list(tuple(UUID, flash_card_indexes[], content{}))
    chat_messages_data = chat_handler.get_chat_messages(
        engine=DB_ENGINE, user_id=user_id, chat_id=chat_id
    )

    if flask.request.method == "GET":
        return [
            chat_response_types.chat_message_to_chat_message_response(
                chat_id=chat_id,
                chat_message_id=cmd[0],
                chat_message=cmd[1],
                saved_flash_card_indexes=cmd[2],
            )
            for cmd in chat_messages_data
        ]

    # POST
    # check chat_messages free limit
    if not user_handler.get_user_is_active(DB_ENGINE, user_id):
        limit = 50
        lookback_date = datetime.now() - timedelta(hours=24)
        count = chat_handler.count_chat_messages(DB_ENGINE, user_id, lookback_date)
        if count >= limit:
            return flask.jsonify({"status": "LIMIT_EXCEEDED"}), 200

    # data to send to openAI
    # fetch most recent messages (the first X in date desc)
    input_messages = [cmd[1] for cmd in chat_messages_data[:CHAT_LOOKBACK]]
    # reverse back into chronological order
    input_messages.reverse()

    data = flask.request.json
    message = data.get("message") if data else None
    new_chat_message = chat_types.ChatMessage(
        role="user",
        content=message,
    )
    input_messages.append(new_chat_message)

    # first get flash_cards messages (openAI format)
    try:
        print(">.............input...............<")
        print(input_messages)
        print(">............................<")
        output_message = PROMPT_FLASHCARDS.fetch(input_messages)
        print(">.............output...............<")
        print(output_message)
        print(">............................<")

        if not (output_message.tool_calls):
            return flask.jsonify({"status": "ERROR"}), 200

        tool_call_args = json.loads(output_message.tool_calls[0].function.arguments)
        if not (tool_call_args["tutor_response"]):
            return flask.jsonify({"status": "ERROR"}), 200

        chat_handler.save_chat_messages(
            engine=DB_ENGINE,
            user_id=user_id,
            chat_id=chat_id,
            chat_messages=[new_chat_message, output_message],
        )
    except Exception as e:
        logger.error(e, exc_info=True)
        flask.abort(Response("Couldn't handle that message", 500))

    return flask.jsonify({"status": "SUCCESS"}), 200


@app.route("/review_flash_card/<flash_card_id>", methods=["POST"])
def review_flash_card(flash_card_id):
    """Updates a flash card after review"""
    current_user_sub = flask.session.get("openid_sub")
    if not current_user_sub:
        flask.abort(Response("Please log in", 401))

    try:
        flash_card_id = uuid.UUID(flash_card_id)
    except ValueError:
        flask.abort(Response("Not a valid id", 404))

    data = flask.request.json
    rating = data.get("rating") if data else None
    assert rating is not None

    try:
        user_id = user_handler.get_user_id(DB_ENGINE, current_user_sub)
        assert user_id is not None

        flash_card_handler.review_flash_card(
            engine=DB_ENGINE,
            user_id=user_id,
            flash_card_id=flash_card_id,
            rating=rating,
        )
    except AssertionError:
        flask.abort(Response("Invalid request", 404))

    return flask.jsonify({"status": "SUCCESS"}), 200


@app.route(
    "/flash_card/<chat_id>/<chat_message_id>/<flash_card_index>", methods=["POST"]
)
def create_or_update_flash_card(chat_id, chat_message_id, flash_card_index):
    """Fetches the chat from the db, and generates a flash_card from the given index"""
    current_user_sub = flask.session.get("openid_sub")
    if not current_user_sub:
        flask.abort(Response("Please log in", 401))

    try:
        chat_id = uuid.UUID(chat_id)
        chat_message_id = uuid.UUID(chat_message_id)
        flash_card_index = int(flash_card_index)
    except ValueError:
        flask.abort(Response("Not a valid id", 404))

    data = flask.request.json
    save = data.get("save") if data else None
    assert save is not None

    try:
        user_id = user_handler.get_user_id(DB_ENGINE, current_user_sub)
        assert user_id is not None

        chat_message = chat_handler.get_chat_message(
            engine=DB_ENGINE,
            user_id=user_id,
            chat_id=chat_id,
            chat_message_id=chat_message_id,
        )
        assert chat_message is not None

        chat_message_response = (
            chat_response_types.chat_message_to_chat_message_response(
                chat_id=chat_id,
                chat_message_id=chat_message_id,
                chat_message=chat_message,
            )
        )

        assert (
            chat_message_response.flash_card_lesson is not None
            and 0
            <= flash_card_index
            < len(chat_message_response.flash_card_lesson.flash_cards)
        )
        flash_card = chat_message_response.flash_card_lesson.flash_cards[
            flash_card_index
        ]

        # write to db
        flash_card_handler.create_or_update_flash_card(
            engine=DB_ENGINE,
            user_id=user_id,
            chat_id=chat_id,
            chat_message_id=chat_message_id,
            flash_card_index=flash_card_index,
            flash_card_lesson=chat_message_response.flash_card_lesson,
            flash_card=flash_card,
            is_active=save,
        )
    except AssertionError:
        flask.abort(Response("Invalid request", 404))

    return flask.jsonify({"status": "SUCCESS", "save": save}), 200


@app.route("/flash_card/<flash_card_id>", methods=["DELETE"])
def delete_flash_card(flash_card_id):
    """Soft-deletes a flash_card by id"""
    current_user_sub = flask.session.get("openid_sub")
    if not current_user_sub:
        flask.abort(Response("Please log in", 401))

    try:
        flash_card_id = uuid.UUID(flash_card_id)
    except ValueError:
        flask.abort(Response("Not a valid flash_card_id", 404))

    try:
        user_id = user_handler.get_user_id(DB_ENGINE, current_user_sub)
        assert user_id is not None

        # write to db
        flash_card_handler.delete_flash_card(
            engine=DB_ENGINE,
            user_id=user_id,
            flash_card_id=flash_card_id,
        )
    except AssertionError:
        flask.abort(Response("Invalid request", 404))

    return flask.jsonify({"status": "SUCCESS"}), 200


@app.route("/flash_cards/<flash_card_status>", methods=["GET"])
def get_flash_cards(flash_card_status: str):
    """Fetches all flash_cards with the new state"""
    current_user_sub = flask.session.get("openid_sub")
    if not current_user_sub:
        flask.abort(Response("Please log in", 401))

    try:
        user_id = user_handler.get_user_id(DB_ENGINE, current_user_sub)
        assert user_id is not None

        user_settings = user_handler.get_user_settings(DB_ENGINE, user_id)
        show_reverse = user_settings.get("show_reverse")

        assert flash_card_status is not None
        flash_card_status = flash_card_status.upper()

        if flash_card_status == "NEW":
            cards = flash_card_handler.get_flash_cards_new(
                DB_ENGINE, user_id, show_reverse=show_reverse
            )
        elif flash_card_status == "REVIEW":
            cards = flash_card_handler.get_flash_cards_review(
                DB_ENGINE, user_id, show_reverse=show_reverse
            )
        elif flash_card_status == "ALL":
            cards = flash_card_handler.get_flash_cards_all(
                DB_ENGINE, user_id, show_reverse=show_reverse
            )
        else:
            flask.abort(Response("Invalid status", 404))
    except AssertionError:
        flask.abort(Response("Invalid request", 404))

    cards_response = [
        flash_card_types.flash_card_to_flash_card_response(card) for card in cards
    ]

    return flask.jsonify(cards_response), 200


@app.route("/flash_card_counts", methods=["GET"])
def get_flash_card_counts():
    """Fetches all flash_cards with the new state"""
    current_user_sub = flask.session.get("openid_sub")
    if not current_user_sub:
        flask.abort(Response("Please log in", 401))

    try:
        user_id = user_handler.get_user_id(DB_ENGINE, current_user_sub)
        assert user_id is not None

        user_settings = user_handler.get_user_settings(DB_ENGINE, user_id)
        show_reverse = user_settings.get("show_reverse")

        card_counts = flash_card_handler.get_flash_card_counts(
            DB_ENGINE, user_id, show_reverse=show_reverse
        )

        res = {"NEW": 0, "DUE": 0, "REVIEW": 0}
        for status, is_due, card_count in card_counts:
            if status == fsrs.State.New.value:
                res["NEW"] += card_count
            else:
                if is_due:
                    res["DUE"] += card_count
                res["REVIEW"] += card_count
        return flask.jsonify(res), 200
    except AssertionError:
        flask.abort(Response("Invalid request", 404))


@app.route("/user_settings", methods=["GET", "POST"])
def user_settings():
    current_user_sub = flask.session.get("openid_sub")
    if not current_user_sub:
        flask.abort(Response("Please log in", 401))

    try:
        user_id = user_handler.get_user_id(DB_ENGINE, current_user_sub)
        assert user_id is not None

        if flask.request.method == "POST":
            data = flask.request.json
            user_handler.save_user_settings(DB_ENGINE, user_id, data)

        user_settings = user_handler.get_user_settings(DB_ENGINE, user_id)
        return flask.jsonify(user_settings), 200

    except AssertionError:
        flask.abort(Response("Invalid request", 404))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=True)
