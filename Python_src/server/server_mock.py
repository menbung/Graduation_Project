from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# In-memory payload that can be updated at runtime
CURRENT_PAYLOAD = {
    'model_id': 1,
    'seeds': [15, 22, 36],
    'k_neighbors': 3,
    'per_seed_top': 3,
    'final_top': 3,
}

# Last result JSON received from client (main.py)
LAST_RECEIVED = None


@app.get('/health')
def health():
    return jsonify({'status': 'ok'})


@app.get('/mock/payload')
def mock_payload_get():
    print(f"[{datetime.now().isoformat()}] GET /mock/payload -> {CURRENT_PAYLOAD}")
    return jsonify(CURRENT_PAYLOAD)


@app.post('/mock/payload')
def mock_payload_set():
    data = request.get_json() or {}
    # Shallow update of the in-memory payload
    if not isinstance(data, dict):
        return jsonify({'error': 'body must be a JSON object'}), 400
    CURRENT_PAYLOAD.update(data)
    print(f"[{datetime.now().isoformat()}] POST /mock/payload <- {data}\n  updated payload: {CURRENT_PAYLOAD}")
    return jsonify({'status': 'updated', 'payload': CURRENT_PAYLOAD})


@app.post('/api/receive')
def api_receive():
    global LAST_RECEIVED
    body = request.get_json(silent=True)
    LAST_RECEIVED = body
    print(f"[{datetime.now().isoformat()}] POST /api/receive <- {body}")
    return jsonify({'status': 'received', 'body': body})


@app.get('/api/received')
def api_received():
    return jsonify({'last_received': LAST_RECEIVED})


if __name__ == '__main__':
    app.run(port=8000)
