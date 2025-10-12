from src.crawler.crawler import crawl_lyrics
from src.clap.clap import process_song_meta
from src.utils.csv_utils import save_df_csv
from src.server.server_client import ServerClient
import pandas as pd


def main_loop():
    # 1) 크롤링
    meta = crawl_lyrics('https://example.com/song/1')

    # 2) CLAP 처리
    processed = process_song_meta(meta)

    # 3) CSV 저장
    df = pd.DataFrame([processed])
    save_df_csv(df, 'data/processed/songs.csv')

    # 4) 서버 전송
    client = ServerClient('http://localhost:8000')
    resp = client.post_results('/api/songs', processed)
    print('server resp:', resp)


if __name__ == '__main__':
    main_loop()
