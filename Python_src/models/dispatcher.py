from typing import Dict, Any, List
from models.knn_model import recommend_with_config_seeds
try:
    # Optional import; used only for model_id == 2
    from feature.fashion_clip import load_fashionclip, rank_images_for_caption, rank_with_prebuilt_index
except Exception:
    load_fashionclip = None  # type: ignore
    rank_images_for_caption = None  # type: ignore

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
        if load_fashionclip is None or rank_images_for_caption is None:
            return {"error": "feature.fashion_clip not available"}

        caption = str(payload.get("caption", "")).strip()
        if not caption:
            return {"error": "caption is required for model_id=2"}

        top_k = int(payload.get("top_k", 20))
        root_dir = payload.get("root_dir", None)
        model_dir = payload.get("model_dir", None)
        scan_limit = payload.get("scan_limit", None)
        try:
            scan_limit = int(scan_limit) if scan_limit is not None else None
        except Exception:
            scan_limit = None
        index_path = payload.get("index_path", None)

        # Ensure model is loaded (no-op if already loaded)
        load_fashionclip(model_dir=model_dir)
        if index_path:
            ranked = rank_with_prebuilt_index(
                caption=caption,
                index_path=index_path,
                top_k=top_k,
                model_dir=model_dir,
            )
        else:
            ranked = rank_images_for_caption(
                caption=caption,
                root_dir=root_dir,
                top_k=top_k,
                model_dir=model_dir,
                scan_limit=scan_limit,
            )

        return {
            "model_id": 2,
            "caption": caption,
            "top_k": top_k,
            "results": [{"path": p, "score": s} for p, s in ranked],
        }

    return {"error": f"Unknown model_id: {model_id}"}