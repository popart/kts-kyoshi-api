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
from handlers import chat_handler


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# log to stdout
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# setup flask app
app = flask.Flask(__name__)
flask_cors.CORS(app)

# init app (ghetto DI)
if os.getenv("ENV") == "PROD":
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


@app.route("/chat_message/<chat_id>", methods=["GET", "POST"])
def chat_message(chat_id):
    try:
        chat_id = uuid.UUID(chat_id)
    except ValueError:
        flask.abort(Response("Not a valid chat id", 404))

    chat_messages = chat_handler.get_chat_messages(DB_ENGINE, chat_id)
    if flask.request.method == "GET":
        return [
            chat_response_types.chat_message_to_chat_message_response(cm)
            for cm in chat_messages
        ]

    message = flask.request.json["message"]
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
            DB_ENGINE,
            chat_id,
            [new_chat_message, output_message],
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
