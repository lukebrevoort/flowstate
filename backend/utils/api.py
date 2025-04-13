from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/test', methods=['GET'])


def test_route():
    return jsonify({"message": "Hello from the backend!"})
if __name__ == '__main__':
    app.run(debug=True, port=5001)