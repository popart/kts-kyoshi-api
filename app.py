import os

from dataclasses import dataclass
import flask
import flask_cors
import json
import logging
import sys

from prompts.prompt_flashcards import get_prompt_flashcards
from clients.chat.openai_chat_client import OpenAIChatClient
from clients.chat.fake_chat_client import FakeChatClient
from clients.chat import chat_types


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
    CHAT_CLIENT = FakeChatClient()
PROMPT_FLASHCARDS = get_prompt_flashcards(CHAT_CLIENT)
CHATS: dict[str, list[chat_types.ChatMessage]] = {}

CHAT_LOOKBACK = -3

@app.route('/', methods=['GET'])
def homepage():
    return 'Ack! What are you doing back here?!'

@app.route('/chat/<chat_id>', methods=['POST'])
def chat(chat_id):
    if chat_id not in CHATS:
        CHATS[chat_id] = []
    chat = CHATS[chat_id]
    logger.info(f"Found chat {chat_id}: {chat}")

    message = flask.request.json['message']
    logger.info(f"Chat {chat_id} new message: {message}")
    new_chat_message = chat_types.ChatMessage(
        role="user",
        content=message,
    )

    input_messages = chat[CHAT_LOOKBACK:].copy()
    input_messages.append(new_chat_message)

    # first get flashcards messages (openAI format)
    try:
        output_message = PROMPT_FLASHCARDS.fetch(input_messages)
        save_result = True
        if output_message.content:
            res = {"message": output_message.content}

            # irrelevant answer should be "..."
            if output_message.content == "...":
                save_result = False
        elif output_message.tool_calls:
            res = json.loads(output_message.tool_calls[0].function.arguments)
            res["input"] = message
        else:
            save_result = False
            logger.error("Bad output message: %s", str(output_message))
            res = {"message": "ERROR: I couldn't handle that message."}

        if save_result:
            chat.append(new_chat_message)
            chat.append(output_message)
    except Exception as e:
        logger.error(e, exc_info=True)
        res = {"message": "ERROR: I couldn't handle that message."}

    return flask.jsonify(res)

@app.route('/flashcard/<chat_id>/<card_index>', methods=['POST'])
def save_flashcard(chat_id, card_index):
    """Fetches the chat from the db, and generates a flashcard from the given index"""
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
