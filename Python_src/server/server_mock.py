import logging
import os
import traceback
import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

DEFAULT_ALLOWED_ORIGINS = ['http://localhost:5173']
_origins_raw = os.environ.get('ALLOWED_ORIGINS', '')
if _origins_raw.strip():
    ALLOWED_ORIGINS = [origin.strip() for origin in _origins_raw.split(',') if origin.strip()]
else:
    ALLOWED_ORIGINS = DEFAULT_ALLOWED_ORIGINS
CORS(
    app,
    resources={r"/api/*": {"origins": ALLOWED_ORIGINS or "*"}},
    supports_credentials=False,
    methods=["GET", "POST", "OPTIONS"],
)

# In-memory payload that can be updated at runtime
CURRENT_PAYLOAD_1 = {
    'model_id': 1,
    'seeds': [10, 20, 30],
    'k_neighbors': 3,
    'per_seed_top': 3,
    'final_top': 3,
}


CURRENT_PAYLOAD_2 = {
    'model_id': 2,
    'song_title': 'Love wins all',
    'artist_name': 'IU',
    'caption':'',
    'top_k': 20,
    'index_path': 'Python_src/feature/fashion_clip_model/image_index.pt',
}

CURRENT_PAYLOAD = CURRENT_PAYLOAD_2
# Last result JSON received from client (main.py)
LAST_RECEIVED = None
# Ring buffer of recent received payloads (time + body)
RECEIVED_LOGS = []  # type: ignore[var-annotated]
MAX_LOGS = 50


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
    now = datetime.now().isoformat()
    print(f"[{now}] POST /api/receive <- {body}")
    # Append to logs (with timestamp)
    RECEIVED_LOGS.append({"time": now, "body": body})
    if len(RECEIVED_LOGS) > MAX_LOGS:
        del RECEIVED_LOGS[0:len(RECEIVED_LOGS) - MAX_LOGS]
    return jsonify({'status': 'received', 'body': body})


@app.get('/api/received')
def api_received():

    return jsonify({
        'last_received': LAST_RECEIVED,
        'count': len(RECEIVED_LOGS),
        'last_time': (RECEIVED_LOGS[-1]['time'] if RECEIVED_LOGS else None),
    })


@app.get('/api/received/all')
def api_received_all():
    # Return all recent logs (time + body)
    return jsonify({'logs': RECEIVED_LOGS})

@app.post('/api/recommend')
def api_recommend():
    """
    Accepts JSON payload and returns model inference result via models.dispatcher.
    """
    try:
        from models.dispatcher import handle_recommendation  # lazy import to avoid startup failures
    except Exception as e:
        return jsonify({'error': f'dispatcher import failed: {e}'}), 500

    payload = request.get_json(silent=True) or {}
    try:
        result = handle_recommendation(payload)
        status = 200 if not (isinstance(result, dict) and 'error' in result) else 400
        return jsonify(result), status
    except Exception as e:
        trace = traceback.format_exc()
        app.logger.error("api_recommend error with payload=%s\n%s", payload, trace)
        print(trace)
        return jsonify({'error': str(e), 'traceback': trace}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', '8000'))
    app.run(host='0.0.0.0', port=port)