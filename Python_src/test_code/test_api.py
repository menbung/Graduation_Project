import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

DEFAULT_BASE_URL = "http://localhost:8000"
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # Python_src
CONTAINER_ROOT = "/app/Python_src"
PAYLOAD_DIR = PROJECT_ROOT / "payloads"
MODEL2_EXTRA_QUERIES = [
    ("빈지노 (Beenzino)", "Aqua Man"),
    ("Mac Miller", "Blue World"),
]


def _pretty_print_json(label: str, data: Dict[str, Any]) -> None:
    print(f"{label}:\n{json.dumps(data, ensure_ascii=False, indent=2)[:4000]}")


def _request(method: str, base_url: str, path: str, **kwargs) -> requests.Response:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    resp = requests.request(method, url, timeout=kwargs.pop("timeout", 60), **kwargs)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        print(f"[ERROR] {method} {url} failed: {exc}")
        if exc.response is not None:
            try:
                _pretty_print_json("[ERROR][RESPONSE_JSON]", exc.response.json())
            except Exception:
                print("[ERROR][RESPONSE_TEXT]", exc.response.text[:4000])
        raise
    return resp


def health_check(base_url: str) -> None:
    print("[INFO] Checking /health ...")
    try:
        resp = _request("GET", base_url, "/health", timeout=5)
        print("[HEALTH]", resp.json())
    except Exception as exc:
        print("[HEALTH][ERROR]", exc)


def send_payload(base_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = _request("POST", base_url, "/api/recommend", json=payload, timeout=120)
    data = resp.json()
    _pretty_print_json("[RESULT]", data)
    return data


def run_model1(base_url: str) -> None:
    payload = {
        "model_id": 1,
        "seeds": [10, 20, 30],
        "k_neighbors": 3,
        "per_seed_top": 3,
        "final_top": 3,
        "vector_cols": ["genre_vector", "mood_vector", "texture_vector"],
    }
    print("\n[TEST] model_id=1")
    send_payload(base_url, payload)


def _use_container_paths(base_url: str) -> bool:
    host = (urlparse(base_url).hostname or "").lower()
    return host not in {"localhost", "127.0.0.1", "0.0.0.0"}


def _build_model2_payload(base_url: str, artist: str, title: str) -> Dict[str, Any]:
    index_path = PROJECT_ROOT / "feature" / "fashion_clip_model" / "image_index.pt"
    root_dir = PROJECT_ROOT / "data" / "cloth"
    use_container_paths = _use_container_paths(base_url)

    def _containerize(path: Path, sub_path: str) -> str:
        if use_container_paths:
            return f"{CONTAINER_ROOT}/{sub_path}"
        return str(path).replace("\\", "/")

    payload: Dict[str, Any] = {
        "model_id": 2,
        "song_title": title,
        "artist_name": artist,
        "top_k": 10,
    }
    if index_path.exists():
        payload["index_path"] = _containerize(
            index_path, "feature/fashion_clip_model/image_index.pt"
        )
    else:
        payload["root_dir"] = _containerize(root_dir, "data/cloth")
        payload["scan_limit"] = 500
    return payload


def run_model2(base_url: str, artist: str = "IU", title: str = "Love wins all") -> None:
    payload = _build_model2_payload(base_url, artist, title)

    print(f"\n[TEST] model_id=2 {artist} - {title}")
    data = send_payload(base_url, payload)
    if isinstance(data, dict):
        items: List[Dict[str, Any]] = data.get("results", []) or []
        if items:
            print(f"[INFO] results_count={len(items)}")
            for i, item in enumerate(items[:5], 1):
                try:
                    score = float(item.get("score", 0.0))
                except Exception:
                    score = 0.0
                path = item.get("path", "")
                print(f"  {i}. {score:.4f}  {path}")

def run_model2_batch(base_url: str, queries: List[tuple[str, str]]) -> None:
    for artist, title in queries:
        run_model2(base_url, artist=artist, title=title)


def run_payload_file(base_url: str, payload_file: Path) -> None:
    if not payload_file.exists():
        print(f"[ERROR] payload file not found: {payload_file}")
        return
    with payload_file.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    print(f"\n[TEST] payload file: {payload_file}")
    send_payload(base_url, payload)


def main() -> None:
    base_url = os.environ.get("BASE_URL", DEFAULT_BASE_URL)
    args = sys.argv[1:]

    print(f"[INFO] Base URL: {base_url}")
    health_check(base_url)

    if not args:
        run_model1(base_url)
        run_model2(base_url)
        return

    for arg in args:
        if arg == "1":
            run_model1(base_url)
        elif arg == "2":
            run_model2(base_url)
        elif arg == "multi2":
            run_model2_batch(base_url, MODEL2_EXTRA_QUERIES)
        elif arg.endswith(".json"):
            run_payload_file(base_url, Path(arg))
        else:
            maybe_file = PAYLOAD_DIR / arg
            if maybe_file.exists():
                run_payload_file(base_url, maybe_file)
            else:
                print(f"[WARN] Unknown argument '{arg}'")


if __name__ == "__main__":
    main()