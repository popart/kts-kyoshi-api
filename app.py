import json
import logging
import os
import sys
import uuid

import flask
import flask_cors
from sqlalchemy import create_engine
from werkzeug.wrappers.response import Response

from prompts.prompt_flashcards import get_prompt_flashcards
from clients.chat.openai_chat_client import OpenAIChatClient
from clients.chat.fake_chat_client import FakeChatClient
from data_types import chat_types, chat_response_types
from handlers import chat_handler, user_handler

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

# setup flask app
app = flask.Flask(__name__)
app.secret_key = SESSION_SECRET_KEY


flask_cors.CORS(app, supports_credentials=True)

# init app (ghetto DI)
if ENV == "PROD":
    CHAT_CLIENT = OpenAIChatClient()
else:
    CHAT_CLIENT = FakeChatClient(response_type=os.getenv("CHAT_TYPE", "CHAT"))
PROMPT_FLASHCARDS = get_prompt_flashcards(CHAT_CLIENT)
CHATS: dict[str, list[chat_types.ChatMessage]] = {}
DB_ENGINE = create_engine(
    "postgresql+psycopg://postgres:mypassword@localhost:5432/kyoshi"
)


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

        return flask.jsonify(
            {
                "message": "Token is valid",
            }
        ), 200

    except ValueError as e:
        return flask.jsonify({"message": str(e)}), 400


@app.route("/check_login", methods=["GET", "POST"])
def check_login():
    is_logged_in = flask.session.get("openid_sub") is not None
    return flask.jsonify({"loggedIn": is_logged_in}), 200


@app.route("/logout", methods=["POST"])
def logout():
    flask.session.clear()  # This clears the entire session
    print("logged out")
    return flask.jsonify({"message": "Logged out successfully"}), 200


@app.route("/chat", methods=["GET", "POST"])
def chat():
    """Returns a list of chats"""
    current_user_sub = flask.session.get("openid_sub")
    if not current_user_sub:
        flask.abort(Response("Please log in", 401))

    user_id = user_handler.get_user_id(DB_ENGINE, current_user_sub)
    assert user_id is not None

    if flask.request.method == "GET":
        return flask.jsonify(chat_handler.get_chats(engine=DB_ENGINE, user_id=user_id))

    chat_handler.create_chat(engine=DB_ENGINE, user_id=user_id)
    return flask.jsonify({"status": "SUCCESS"}), 200


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

    chat_messages = chat_handler.get_chat_messages(
        engine=DB_ENGINE, user_id=user_id, chat_id=chat_id
    )

    if flask.request.method == "GET":
        return [
            chat_response_types.chat_message_to_chat_message_response(cm)
            for cm in chat_messages
        ]

    data = flask.request.json
    message = data.get("message") if data else None
    logger.info(f"Chat {chat_id} new message: {message}")
    new_chat_message = chat_types.ChatMessage(
        role="user",
        content=message,
    )

    input_messages = chat_messages[CHAT_LOOKBACK:].copy()
    input_messages.append(new_chat_message)

    # first get flashcards messages (openAI format)
    try:
        output_message = PROMPT_FLASHCARDS.fetch(input_messages)

        if not (output_message.content or output_message.tool_calls):
            logger.error("Bad output message: %s", str(output_message))
            flask.abort(Response("Couldn't handle that message", 404))

        chat_handler.save_chat_messages(
            engine=DB_ENGINE,
            user_id=user_id,
            chat_id=chat_id,
            chat_messages=[new_chat_message, output_message],
        )
    except Exception as e:
        logger.error(e, exc_info=True)
        flask.abort(Response("Couldn't handle that message", 404))

    return Response({"status": "SUCCESS"}, 200)


@app.route("/flashcard/<chat_id>/<card_index>", methods=["POST"])
def save_flashcard(chat_id, card_index):
    """Fetches the chat from the db, and generates a flashcard from the given index"""
    pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=True)
