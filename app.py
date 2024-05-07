from flask import Flask, request
from flask_cors import CORS
from flask import jsonify


# setup flask app
app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def homepage():
    return 'Ack! What are you doing back here?!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
