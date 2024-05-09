from dataclasses import dataclass
import flask
import flask_cors
import json
import logging
import sys

from prompts.prompt_flashcards import flashcards_prompt


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# log to stdout
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# setup flask app
app = flask.Flask(__name__)
flask_cors.CORS(app)

# TODO: replace w/ a db
# dict[str, list[message]]
CHATS = {}

@dataclass
class ChatMessage:
    content: str

@app.route('/', methods=['GET'])
def homepage():
    return 'Ack! What are you doing back here?!'

@app.route('/chat/<chat_id>', methods=['POST'])
def chat(chat_id):
    message = flask.request.json['message']  # what's the format? for now a str
    logger.info(f"Chat {chat_id} new message: {message}")

    # TODO: add some context messages from the CHATS db
    #       required if you want to ask questions about the flashcards
    input_messages = [{"role": "user", "content": message }]

    # first get flashcards messages (openAI format)
    try:
        output_messages = flashcards_prompt.fetch(input_messages)
        first_output = output_messages[0]
        if "content" in first_output:
            content_output = {"message": first_output["content"]}
        elif "tool_calls" in first_output:
            content_output = json.loads(first_output["tool_calls"][0].function.arguments)
            content_output["input"] = message
        else:
            logger.error("Bad output message: %s", str(output_messages))
            content_output = {"message": "ERROR: I couldn't handle that message."}
    except Exception as e:
        logger.error(e, exc_info=True)
        content_output = {"message": "ERROR: I couldn't handle that message."}

    # TODO: save messages to CHATS db (openAI format)
    #       actually no reason to save the tool call responses... can generate them anyways
    #       need to return the message ids so it's easy to save flashcards

    return flask.jsonify(content_output)

@app.route('/flashcard/<chat_id>/<card_index>', methods=['POST'])
def save_flashcard(chat_id, card_index):
    """Fetches the chat from the db, and generates a flashcard from the given index"""
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
