from typing import Dict, Any, List
from models.knn_model import recommend_with_config_seeds

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
        # TODO: 구현자 채움 (예: 옷 3개 이미지/태그 기반 FashionCLIP 추천)
        # from feature.fashion_clip import recommend_with_fashionclip
        # return recommend_with_fashionclip(payload)
        return {"error": "FashionCLIP not implemented yet"}

    return {"error": f"Unknown model_id: {model_id}"}