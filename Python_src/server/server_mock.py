from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/songs', methods=['POST'])
def receive_songs():
    data = request.get_json()
    return jsonify({'status': 'ok', 'received': data})

if __name__ == '__main__':
    app.run(port=8000)
