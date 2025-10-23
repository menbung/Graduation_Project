### 프로젝트 개요
- 이 프로그램은 서버에서 JSON payload를 받아 모델을 실행(KNN/FashionCLIP)하고 결과를 반환합니다.
- 실제 동작은 payload의 `model_id`로 분기합니다. `1=KNN`, `2=FashionCLIP(추후)`.

## 필수 설치(Requirements)
- Python 3.10+ 권장
- 패키지
  - scikit-learn>=1.4
  - joblib>=1.3
  - numpy>=1.23
  - requests>=2.31
  - Flask>=3.0   (모의 서버 사용 시)
  - python-dotenv>=1.0
  - pandas>=2.0  (main.py에서 import)

설치 예시(Windows PowerShell):
```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -U scikit-learn joblib numpy requests Flask python-dotenv pandas
```

## 환경변수(Environment)
- `CSV_SONGS_PATH`: 곡 메타 CSV의 절대/상대 경로 (기본: `Python_src/data/songs_out_final.csv`)

python Python_src/main.py --knn \
  --payload_url https://REAL_SERVER/api/payload \
  --watch --interval 5 \
  --post_url https://REAL_SERVER/api/receive
```
- 인증이 필요하면 서버 구현 또는 main의 `requests.get/post` 호출에 헤더 추가:
```python
headers={'Authorization': 'Bearer <TOKEN>'}
```

## JSON 계약(Contract)
### 받는 JSON (server → program)
- GET `/api/payload`
- Content-Type: application/json
```json
{
  "model_id": 1,
  "seeds": [15, 22, 36],
  "k_neighbors": 3,
  "per_seed_top": 3,
  "final_top": 3
}
```
- 규칙: `model_id=1`일 때 `seeds`는 정수 3개 필수

### 보내는 JSON (program → server)
- POST `/api/receive`
- Content-Type: application/json
```json
{
  "model_id": 1,
  "seed_titles": ["toxic till the end", "끝", "우리들의 블루스"],
  "final_top_labels": ["미니멀 / Minimal Fashion", "캐주얼 / Casual", "스트릿 / Street Fashion"],
  "final_top_genres": ["Soul", "Pop", "Ambient"],
  "per_seed_top_labels": [
    ["미니멀 / Minimal Fashion", "캐주얼 / Casual", "스트릿 / Street Fashion"],
    ["캐주얼 / Casual", "시크 / Chic Fashion", "미니멀 / Minimal Fashion"],
    ["캐주얼 / Casual", "스트릿 / Street Fashion", "미니멀 / Minimal Fashion"]
  ],
  "per_seed_top_genres": [
    ["Indie Pop", "Pop", "Soul"],
    ["Ambient", "Soul", "Blues"],
    ["Pop", "Soul", "Country"]
  ]
}
```

- 모델 분기: `models/dispatcher.py`의 `handle_recommendation(payload)`가 `model_id`로 분기
- KNN 추천: `models/knn_model.py`의 `recommend_*` 함수 사용
- 고정 CSV 경로: `config.CSV_SONGS_PATH` (환경변수로 오버라이드 가능)


2025-10-14

해야하는 일
fashion clip 모델저장할때 허깅스페이스 형식으로 저장해야하는데 그렇게 안해서
안돌아감



서버에서 데이터 주는 형식

서버는 그냥 런

클라이언트 실행 knn


python .\Python_src\main.py --knn --payload_url http://localhost:8000/mock/payload --post_url http://localhost:8000/api/receive
