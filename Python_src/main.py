import pandas as pd
import argparse

# Optional import for KNN recommendation (kept isolated to avoid breaking existing flow)
try:
    from models.knn_model import recommend_from_csv_with_indices, recommend_with_config_seeds
    ##여기서 임포트 한게 뭐지??
    ##첫번째 함수는 csv_path와 시드 3개를 받아서 knn 추천을 실행하는 함수
    ## config seeds는 csv경로를 고정경로를 사용해서 시드 3래로 knn 추천실행
except Exception:
    recommend_from_csv_with_indices = None  # type: ignore
    recommend_with_config_seeds = None  # type: ignore

# Optional dispatcher (model_id 기반 분기)
try:
    from models.dispatcher import handle_recommendation
    ##여기서 임포트 한게 뭐지?
    ##이 함수는 model id로 분기를 실행한 후에 그에 따른 함수를 실행하고 결과를 출력한다
    ##model id 1이면 knn 2이면 fashionclip
except Exception:
    handle_recommendation = None  # type: ignore

def main_loop():
    
    parser = argparse.ArgumentParser(description='App entry with optional KNN demo')
    parser.add_argument('--knn', action='store_true', help='Run KNN recommendation demo instead of crawl loop')
    parser.add_argument('--csv_path', default='Python_src/data/songs_out_final.csv', help='CSV path for KNN demo (project-relative ok)')
    #csv path 경로 기본 상대경로 사용해야함
    parser.add_argument('--seeds', nargs='+', type=int, default=[15, 22, 36], help='Three seed indices for KNN demo')
    parser.add_argument('--seeds_json', type=str, default=None, help='Path to a JSON file containing {"seeds":[a,b,c]}')
    #시드가 뭔지 확인
    parser.add_argument('--payload_json', type=str, default=None, help='Path to a JSON file containing full payload (e.g., {"model_id":1, ...})')
    parser.add_argument('--payload_url', type=str, default=None, help='HTTP URL to fetch payload JSON (e.g., http://localhost:8000/mock/payload)')
    #payload가 뭐지?
    #jason 객채를 payload라고 한다
    #payload url --> http get으로 페이로드를 가져올 url 
    parser.add_argument('--watch', action='store_true', help='Continuously poll payload_url and process incoming JSON')
    #wach --> payload url을 주기적으로 폴링, 서버에서 주는 jasondata를 주기적으로 받는 역할
    #주기적으로 가 아니라 그냥 올때 마다 확인 해야할 거 같다 여러명에서 데이터를 동시에 주면??

    parser.add_argument('--interval', type=float, default=5.0, help='Polling interval seconds when --watch is used')
    parser.add_argument('--max_iters', type=int, default=0, help='Max iterations when --watch is used (0=infinite)')
    #폴링 횟수 제한
    #폴링 주기
    parser.add_argument('--k_neighbors', type=int, default=3)
    parser.add_argument('--per_seed_top', type=int, default=3)
    parser.add_argument('--final_top', type=int, default=3)
    #final top --> 최종 결과 개수
    #per seed top --> 각 시드에서 추천된 결과 개수
    #k neighbors --> k 개수
    #post url --> 결과를 서버에 보낼 url
    parser.add_argument('--post_url', type=str, default=None, help='HTTP URL to POST KNN result (styles/genres) as JSON')
    args, _unknown = parser.parse_known_args()

    if args.knn:
        #실행모드 knn인 경우 분기
        if recommend_from_csv_with_indices is None:
            raise RuntimeError('models.knn_model not available; cannot run KNN demo')
        # Prefer full payload if provided (dispatcher handles model_id branching)
        if args.payload_json or args.payload_url:
            import json
            if handle_recommendation is None:
                raise RuntimeError('models.dispatcher not available; cannot handle payload_json')
            if args.payload_json:
                with open(args.payload_json, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                result = handle_recommendation(payload)
            else:
                import requests, time
                iters = 0
                def _fetch_and_process():
                    r = requests.get(args.payload_url, timeout=5)
                    r.raise_for_status()
                    p = r.json()
                    res = handle_recommendation(p)
                    print('[PAYLOAD]', p)
                    try:
                        print('[INFO] dispatcher model_id:', int(p.get('model_id', 1)))
                    except Exception:
                        print('[INFO] dispatcher model_id:', p.get('model_id'))
                    print('[RESULT] final top styles:', res.get('final_top_labels', []))
                    if 'final_top_genres' in res:
                        print('[RESULT] final top genres:', res.get('final_top_genres', []))
                    if 'error' in res:
                        print('[ERROR] dispatcher:', res.get('error'))
                    # Fashion-CLIP (model_id=2) result preview
                    if isinstance(res, dict) and 'results' in res:
                        items = res.get('results', []) or []
                        print(f"[INFO] Fashion-CLIP results count: {len(items)}")
                        print('[RESULT] Fashion-CLIP top results:')
                        for i, item in enumerate(items[:20], 1):
                            try:
                                score = float(item.get('score', 0.0))
                            except Exception:
                                score = 0.0
                            path = item.get('path', '')
                            print(f'  {i}. {score:.4f}  {path}')
                    return res
                if args.watch:
                    try:
                        last_res = {}
                        while True:
                            last_res = _fetch_and_process() or {}
                            iters += 1
                            if args.max_iters and iters >= args.max_iters:
                                break
                            time.sleep(max(0.0, args.interval))
                    except KeyboardInterrupt:
                        print('Stopped watching payload_url')
                    result = last_res
                else:
                    result = _fetch_and_process() or {}
        else:
            seeds = args.seeds
            if args.seeds_json:
                import json
                with open(args.seeds_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                seeds = data.get('seeds', seeds)
            if len(seeds) != 3:
                raise ValueError('--seeds or seeds_json must provide exactly 3 integers')
            if recommend_with_config_seeds is not None and args.csv_path == 'Python_src/data/songs_out_final.csv':
                # Prefer config-based path when using default
                result = recommend_with_config_seeds(
                    seeds=seeds,
                    k_neighbors=args.k_neighbors,
                    per_seed_top=args.per_seed_top,
                    final_top=args.final_top,
                    vector_cols=["genre_vector", "mood_vector", "texture_vector"],
                )
            else:
                result = recommend_from_csv_with_indices(
                    csv_path=args.csv_path,
                    a=seeds[0],
                    b=seeds[1],
                    c=seeds[2],
                    k_neighbors=args.k_neighbors,
                    per_seed_top=args.per_seed_top,
                    final_top=args.final_top,
                    vector_cols=["genre_vector", "mood_vector", "texture_vector"],
                )
        seed_titles = result.get('seed_titles', [])
        neighbor_titles = result.get('per_seed_neighbor_titles', [])
        per_seed_labels = result.get('per_seed_top_labels', [])
        per_seed_genres = result.get('per_seed_top_genres', [])
        final_labels = result.get('final_top_labels', [])
        final_genres = result.get('final_top_genres', [])

        print('[RESULT] Seeds:')
        for i, st in enumerate(seed_titles, 1):
            print(f'  Seed#{i} title: {st}')
        print('[RESULT] per-seed neighbors (titles):')
        for i, nt in enumerate(neighbor_titles, 1):
            print(f'  Seed#{i} neighbors: {nt}')
        print('[RESULT] per-seed top styles:')
        for i, labels in enumerate(per_seed_labels, 1):
            print(f'  Seed#{i}: {labels}')
        if per_seed_genres:
            print('[RESULT] per-seed top genres:')
            for i, genres in enumerate(per_seed_genres, 1):
                print(f'  Seed#{i}: {genres}')
        print(f'[RESULT] final top styles: {final_labels}')
        if final_genres:
            print(f'[RESULT] final top genres: {final_genres}')
        # Optional: POST result JSON to server
        if args.post_url:
            try:
                import requests
                from pathlib import Path
                # If Fashion-CLIP result (has image 'results'), convert paths to project-root-relative
                if isinstance(result, dict) and 'results' in result:
                    project_root = Path(__file__).resolve().parent.parent
                    converted = []
                    for item in result.get('results', []) or []:
                        p = item.get('path', '')
                        s = item.get('score', 0.0)
                        try:
                            abs_p = Path(p).resolve()
                            rel_p = abs_p.relative_to(project_root)
                            rel_str = rel_p.as_posix()
                        except Exception:
                            # Fallback to posix string of given path
                            rel_str = Path(p).as_posix()
                        converted.append({'path': rel_str, 'score': float(s)})
                    out_json = {
                        'model_id': result.get('model_id', 2),
                        'caption': result.get('caption', ''),
                        'top_k': result.get('top_k', len(converted)),
                        'results': converted,
                    }
                else:
                    # KNN payload (keep prior shape)
                    out_json = {
                        'model_id': 1,
                        'seed_titles': seed_titles,
                        'final_top_labels': final_labels,
                        'final_top_genres': final_genres,
                    }
                r = requests.post(args.post_url, json=out_json, timeout=5)
                r.raise_for_status()
                print('[POST] sent to', args.post_url, 'status:', r.status_code)
            except Exception as e:
                print('[POST][ERROR]', e)
    else:
        print('Nothing to run. Use --knn to run the KNN demo.')


if __name__ == '__main__':
    main_loop()
