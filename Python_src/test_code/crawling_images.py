import sys
sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')

# selenium 임포트 및 셋업
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import pandas as pd

chrome_options = Options()
chrome_options.add_argument("--headless") # GUI 없는 환경
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 드라이버 실행
driver = webdriver.Chrome(options=chrome_options)


import os

def save_song_info_to_drive(singer, title, album, release_date, genre, like_count, lyrics):
    # 구글 드라이브 내 기본 저장 경로
    base_path = "/content/drive/MyDrive/graduateproject/music_data"

    # 폴더명과 파일명: 공백과 특수문자 제거
    safe_singer = singer.replace(" ", "_").replace("/", "-")
    safe_title = title.replace(" ", "_").replace("/", "-")
    folder_name = f"{safe_singer}_{safe_title}"

    # 최종 폴더 경로 생성
    folder_path = os.path.join(base_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # 파일 경로 설정
    filename = f"info_{safe_title}_{safe_singer}.txt"
    file_path = os.path.join(folder_path, filename)

    # 텍스트 저장
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"곡 제목: {title}\n")
        f.write(f"가수: {singer}\n")
        f.write(f"앨범: {album}\n")
        f.write(f"발매일: {release_date}\n")
        f.write(f"장르: {genre}\n")
        f.write(f"좋아요 수: {like_count}\n")
        f.write("\n[가사]\n")
        f.write(lyrics)

    print(f"✅ 저장 완료: {file_path}")

def crawl_song_info(driver, artist_name, max_count=5):


    all_songs = []

    # 멜론 메인 접속
    driver.get("https://www.melon.com/")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "top_search"))
    )

    # 검색
    search_input = driver.find_element(By.ID, "top_search")
    search_input.send_keys(artist_name)
    search_input.send_keys(Keys.ENTER)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//a[@title="곡 - 페이지 이동"]'))
    )

    # '곡' 탭 클릭
    song_tab = driver.find_element(By.XPATH, '//a[@title="곡 - 페이지 이동"]')
    song_tab.click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.tb_list.d_song_list.songTypeOne table tbody tr"))
    )

    # 곡 리스트 추출
    songs = driver.find_elements(By.CSS_SELECTOR, "div.tb_list.d_song_list.songTypeOne table tbody tr")
    print(f"총 곡 수: {len(songs)}")

    for i, song in enumerate(songs[:max_count]):
        try:
            title_elem = song.find_element(By.CSS_SELECTOR, "a.fc_gray")
            title = title_elem.get_attribute("title")

            detail_link_elem = song.find_element(By.CSS_SELECTOR, "a.btn_icon_detail")
            onclick = detail_link_elem.get_attribute("href")
            match = re.search(r"goSongDetail\('(\d+)'\)", onclick)

            if match:
                song_id = match.group(1)
                url = f"https://www.melon.com/song/detail.htm?songId={song_id}"
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.thumb#d_song_org img"))
                )

                try:
                    album_img_url = driver.find_element(By.CSS_SELECTOR, "div.thumb#d_song_org img").get_attribute("src")
                    title = driver.find_element(By.CSS_SELECTOR, "div.song_name").text.strip()
                    singer = driver.find_element(By.CSS_SELECTOR, "div.artist a.artist_name").text.strip()
                    album = driver.find_element(By.CSS_SELECTOR, "div.meta dl.list > dd:nth-of-type(1)").text.strip()

                    print(f"🎵 {i+1}. {title} 앨범 이미지 URL 수집")

                    all_songs.append({
                        "title": title,
                        "singer": singer,
                        "album": album,
                        "album_img_url": album_img_url
                    })

                except Exception as e:
                    print(f"❌ 상세 정보(이미지) 추출 실패: {e}")

                driver.back()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.tb_list.d_song_list.songTypeOne table tbody tr"))
                )
                songs = driver.find_elements(By.CSS_SELECTOR, "div.tb_list.d_song_list.songTypeOne table tbody tr")

        except Exception as e:
            print(f"{i+1}. ❌ 에러 발생: {e}")

    return all_songs
def save_album_image(singer, title, album, album_img_url, save_dir, index_prefix=None):
    import os
    import re
    import requests

    os.makedirs(save_dir, exist_ok=True)

    try:
        # 해상도 업
        album_img_url = album_img_url.replace("/resize/282", "/resize/1000")

        # 파일명 안전화
        safe_singer = re.sub(r'[\\/:*?"<>|]', '_', singer)
        safe_album = re.sub(r'[\\/:*?"<>|]', '_', album)
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
        prefix = f"{index_prefix}_" if index_prefix is not None else ""
        # 번호_가수이름_곡제목_앨범이름.jpg
        filename = f"{prefix}{safe_singer}_{safe_title}_{safe_album}.jpg"
        img_path = os.path.join(save_dir, filename)

        # 이미지 다운로드
        img_data = requests.get(album_img_url).content
        with open(img_path, "wb") as f:
            f.write(img_data)

        print(f"🖼️ 앨범 이미지 저장 완료: {filename}")
        return filename

    except Exception as e:
        print(f"❌ 이미지 저장 실패 ({title}): {e}")
        return None

def _normalize(text):
    if text is None:
        return ""
    return re.sub(r"\s+", "", str(text)).strip().lower()

def download_album_image_for(driver, artist_name, title, save_dir, row_index, max_count=1):
    """
    아티스트 이름으로 검색한 후 목록에서 제목과 가장 잘 매칭되는 곡을 선택해 앨범 이미지를 저장.
    """
    try:
        songs = crawl_song_info(driver, artist_name, max_count=max_count)
        if not songs:
            print(f"⚠️ 결과 없음: {artist_name} - {title}")
            return False

        norm_target_title = _normalize(title)
        norm_target_artist = _normalize(artist_name)

        best = None
        # 1순위: 제목 완전일치 + 가수 부분일치
        for s in songs:
            if _normalize(s.get("title")) == norm_target_title and norm_target_artist in _normalize(s.get("singer")):
                best = s
                break
        # 2순위: 제목 완전일치
        if best is None:
            for s in songs:
                if _normalize(s.get("title")) == norm_target_title:
                    best = s
                    break
        # 3순위: 첫 번째 결과
        if best is None:
            best = songs[0]

        if not best.get("album_img_url"):
            print(f"⚠️ 이미지 URL 없음: {artist_name} - {title}")
            return False

        saved = save_album_image(best["singer"], best["title"], best["album"], best["album_img_url"], save_dir, index_prefix=row_index)
        return saved is not None
    except Exception as e:
        print(f"❌ 처리 실패 ({artist_name} - {title}): {e}")
        return False

def process_csv_and_download_images(csv_path, save_dir, artist_col_candidates=None, title_col_candidates=None, limit=None):
    """
    CSV를 읽어 (아티스트, 제목)으로 멜론을 검색하고 앨범 이미지를 저장.
    """
    if artist_col_candidates is None:
        artist_col_candidates = ["artist", "singer", "artist_name", "가수"]
    if title_col_candidates is None:
        title_col_candidates = ["title", "song", "track", "곡명", "제목"]

    df = pd.read_csv(csv_path)
    cols = [c for c in df.columns]

    artist_col = next((c for c in artist_col_candidates if c in df.columns), None)
    title_col = next((c for c in title_col_candidates if c in df.columns), None)
    if artist_col is None or title_col is None:
        raise ValueError(f"CSV 컬럼을 찾지 못했습니다. 사용 가능한 컬럼: {cols}")

    os.makedirs(save_dir, exist_ok=True)

    total = len(df) if limit is None else min(limit, len(df))
    print(f"총 {total}개 항목 처리 시작 (CSV: {csv_path})")

    processed = 0
    for idx, row in df.iterrows():
        if limit is not None and processed >= limit:
            break
        artist_name = str(row[artist_col])
        title = str(row[title_col])
        print(f"\n🎵 {processed+1}. {artist_name} - {title}")
        ok = download_album_image_for(driver, artist_name, title, save_dir, row_index=processed+1, max_count=1)
        processed += 1

    print(f"\n✅ 완료: {processed}/{total} 항목 처리")

if __name__ == "__main__":
    # 프로젝트 루트 기준 상대 경로 (Python_src에서 실행 가정)
    csv_path = os.path.join("data", "songs_out_final.csv")
    save_dir = os.path.join("data", "album_images")
    try:
        process_csv_and_download_images(csv_path, save_dir, limit=None)
    finally:
        try:
            driver.quit()
        except:
            pass