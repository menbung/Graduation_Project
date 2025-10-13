졸업 프로젝트

실행시에 arg로 url을 서버 url로 바꾸면 된다.


    python Python_src/main.py --knn --payload_url https://REAL/api/payload --watch --interval 5 --post_url https://REAL/api/receive
    ```

- 권장 정리
  - `Python_src/server/server_mock.py`: 더 이상 사용 안 함(로컬 테스트용만 유지).
  - `Python_src/config.py`: 운영환경에서 쓰면 좋을 값들을 환경변수로 관리
    - 예: `CSV_SONGS_PATH`, `API_BASE_URL`, `API_TOKEN` 등.
  - 인증/헤더 필요 시:
    - `Python_src/server/server_client.py`에 헤더 추가해서 사용하거나,
    - 현재 `main.py`의 `requests.get/post(...)` 호출에 `headers={'Authorization': 'Bearer ...'}` 추가.

- 서버 계약 그대로 유지
  - Pull: GET `/api/payload` → { model_id, seeds, ... }
  - Push: POST `/api/receive` ← { model_id, seed_titles, final_top_labels, final_top_genres, ... }

- 선택(운영 모드 변경 시)
  - 폴링 대신 서버가 프로그램으로 푸시(Webhook)할 계획이면, Flask/FastAPI로 수신 엔드포인트를 이 프로그램에 추가하고 `--watch` 경로는 사용하지 않습니다.