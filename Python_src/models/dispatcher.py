from typing import Dict, Any, List
from models.knn_model import recommend_with_config_seeds
from config import MP3_OUTPUT_DIR  # type: ignore
try:
    # Optional import; used only for model_id == 2
    from feature.fashion_clip import load_fashionclip, rank_images_for_caption, rank_with_prebuilt_index
except Exception:
    load_fashionclip = None  # type: ignore
    rank_images_for_caption = None  # type: ignore
try:
    from crawler.youtubeCrawler import download_mp3_from_youtube
except Exception:
    download_mp3_from_youtube = None  # type: ignore
try:
    # Optional stub for Melon crawling
    from crawler.melonCrawler import extract_lyrics_and_images
except Exception:
    extract_lyrics_and_images = None  # type: ignore
try:
    # CLAP-based caption generator (stub)
    from models.clap_caption import generate_caption_with_clap
except Exception:
    generate_caption_with_clap = None  # type: ignore

##main에서 json 데이터를 받았을때 모델 번호를 받아서 기능을 분기하는 함수
##1번이면 knn사용 2번이면 fashionclip 사용

def handle_recommendation(payload: Dict[str, Any]) -> Dict[str, Any]:
    model_id = int(payload.get("model_id", 1))

    if model_id == 1:
        seeds: List[int] = payload.get("seeds", [])
        return recommend_with_config_seeds(
            seeds=seeds,
            k_neighbors=int(payload.get("k_neighbors", 3)),
            per_seed_top=int(payload.get("per_seed_top", 3)),
            final_top=int(payload.get("final_top", 3)),
            vector_cols=["genre_vector", "mood_vector", "texture_vector"],
        )

    elif model_id == 2:
        print("[DISPATCH] model_id=2 start")
        if load_fashionclip is None or rank_images_for_caption is None:
            return {"error": "feature.fashion_clip not available"}

        # Derive query from song_title + artist_name (no direct caption from payload)
        song_title = str(payload.get("song_title", "")).strip()
        artist_name = str(payload.get("artist_name", "")).strip()
        combined_query = f"{artist_name} {song_title}".strip()
        print(f"[DISPATCH] combined_query='{combined_query}'")
        if not combined_query:
            return {"error": "song_title or artist_name required for model_id=2"}

        top_k = int(payload.get("top_k", 20))
        root_dir = payload.get("root_dir", None)
        model_dir = payload.get("model_dir", None)
        scan_limit = payload.get("scan_limit", None)
        try:
            scan_limit = int(scan_limit) if scan_limit is not None else None
        except Exception:
            scan_limit = None
        index_path = payload.get("index_path", None)

        # 1) Download audio (mp3) using YouTube for combined query
        audio_dir: str | None = None
        if download_mp3_from_youtube is not None:
            try:
                audio_dir = download_mp3_from_youtube(combined_query, output_dir=MP3_OUTPUT_DIR)
                print(f"[DISPATCH] audio_dir='{audio_dir}'")
            except Exception:
                audio_dir = None
                print("[DISPATCH][WARN] audio download failed.")

        # 2) Trigger Melon crawler to extract lyrics (stubbed)
        lyrics_text: str | None = None
        if extract_lyrics_and_images is not None:
            try:
                lyrics_text = extract_lyrics_and_images(combined_query, output_dir=audio_dir)
                print(f"[DISPATCH] lyrics_len={len(lyrics_text) if lyrics_text else 0}")
            except Exception:
                lyrics_text = None
                print("[DISPATCH][WARN] lyrics fetch failed.")

        # 3) Generate caption using CLAP (audio + lyrics)
        caption = combined_query
        if generate_caption_with_clap is not None and audio_dir:
            try:
                clap_caption = generate_caption_with_clap(audio_dir=audio_dir, lyrics_text=lyrics_text or "")
                if isinstance(clap_caption, str) and clap_caption.strip():
                    caption = clap_caption.strip()
                print(f"[DISPATCH] caption='{caption[:120]}{'...' if len(caption)>120 else ''}'")
            except Exception:
                pass

        # Ensure model is loaded (no-op if already loaded)
        print("[DISPATCH] Loading Fashion-CLIP...")
        load_fashionclip(model_dir=model_dir)
        if index_path:
            print(f"[DISPATCH] Using prebuilt index: {index_path}")
            ranked = rank_with_prebuilt_index(
                caption=caption,
                index_path=index_path,
                top_k=top_k,
                model_dir=model_dir,
            )
        else:
            print(f"[DISPATCH] Scanning images under root_dir='{root_dir}' (may be slow)")
            ranked = rank_images_for_caption(
                caption=caption,
                root_dir=root_dir,
                top_k=top_k,
                model_dir=model_dir,
                scan_limit=scan_limit,
            )

        print(f"[DISPATCH] Ranked results: {len(ranked)}")
        return {
            "model_id": 2,
            "caption": caption,
            "top_k": top_k,
            "results": [{"path": p, "score": s} for p, s in ranked],
            "audio_dir": audio_dir,
            "lyrics": lyrics_text,
        }

    return {"error": f"Unknown model_id: {model_id}"}