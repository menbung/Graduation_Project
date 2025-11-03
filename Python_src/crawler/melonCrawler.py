from config import SONGS_OUT_NEW_CSV  # type: ignore
from pathlib import Path
import os
import re
from typing import Optional

import pandas as pd  # type: ignore


def extract_lyrics_and_images(query: str, output_dir: str | None = None) -> str | None:
    """
    Fetch lyrics text for the top-1 Melon search result for the query
    ("artist_name song_title"). Images are not handled.

    Returns:
        lyrics_text (str | None): Extracted lyrics, or None if not found.
    Side effects:
        Appends a single row to SONGS_OUT_NEW_CSV (UTF-8) with the song info.
    """
    print(f"[MELON] Start fetch. query='{query}'")
    # Lazy import selenium to avoid hard dependency at module import time
    try:
        from selenium import webdriver  # type: ignore
        from selenium.webdriver.chrome.options import Options  # type: ignore
        from selenium.webdriver.common.by import By  # type: ignore
        from selenium.webdriver.common.keys import Keys  # type: ignore
        from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
        from selenium.webdriver.support import expected_conditions as EC  # type: ignore
    except Exception:
        return None

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)

        driver.get("https://www.melon.com/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "top_search")))
        print("[MELON] Opened homepage.")

        search_input = driver.find_element(By.ID, "top_search")
        search_input.clear()
        search_input.send_keys(query)
        search_input.send_keys(Keys.ENTER)
        print("[MELON] Submitted search.")

        # Click "곡" tab if present
        try:
            song_tab = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, '//a[@title="곡 - 페이지 이동"]'))
            )
            song_tab.click()
            print("[MELON] Clicked '곡' tab.")
        except Exception:
            pass

        # Wait for song list and take the first row
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.tb_list.d_song_list.songTypeOne table tbody tr"))
        )
        rows = driver.find_elements(By.CSS_SELECTOR, "div.tb_list.d_song_list.songTypeOne table tbody tr")
        if not rows:
            return None
        print(f"[MELON] Found {len(rows)} results. Picking top-1.")

        row = rows[0]
        # Navigate to detail
        try:
            detail_link = row.find_element(By.CSS_SELECTOR, "a.btn_icon_detail")
            href = detail_link.get_attribute("href") or ""
            m = re.search(r"goSongDetail\('(\d+)'\)", href)
            if m:
                song_id = m.group(1)
                driver.get(f"https://www.melon.com/song/detail.htm?songId={song_id}")
                print(f"[MELON] Opened detail page. song_id={song_id}")
            else:
                title_link = row.find_element(By.CSS_SELECTOR, "a.fc_gray")
                title_link.click()
                print("[MELON] Clicked title link to detail page.")
        except Exception:
            try:
                title_link = row.find_element(By.CSS_SELECTOR, "a.fc_gray")
                title_link.click()
                print("[MELON] Fallback: clicked title link.")
            except Exception:
                return None

        # Extract fields
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.song_name")))
        title = driver.find_element(By.CSS_SELECTOR, "div.song_name").text.strip()
        try:
            singer = driver.find_element(By.CSS_SELECTOR, "div.artist a.artist_name").text.strip()
        except Exception:
            singer = driver.find_element(By.CSS_SELECTOR, "div.artist").text.strip()
        album = driver.find_element(By.CSS_SELECTOR, "div.meta dl.list > dd:nth-of-type(1)").text.strip()
        release_date = driver.find_element(By.CSS_SELECTOR, "div.meta dl.list > dd:nth-of-type(2)").text.strip()
        genre = driver.find_element(By.CSS_SELECTOR, "div.meta dl.list > dd:nth-of-type(3)").text.strip()
        try:
            like_count = driver.find_element(By.CSS_SELECTOR, "span#d_like_count").text.strip().replace(",", "")
        except Exception:
            like_count = "0"
        try:
            lyrics = driver.find_element(By.ID, "d_video_summary").text.strip()
        except Exception:
            lyrics = None
        print(f"[MELON] Parsed detail. title='{title}' singer='{singer}' lyrics_len={len(lyrics) if lyrics else 0}")

        # Append row to CSV
        csv_path = Path(SONGS_OUT_NEW_CSV)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        exists = csv_path.exists()
        row_dict = {
            "title": title,
            "singer": singer,
            "album": album,
            "release_date": release_date,
            "genre": genre,
            "like_count": like_count,
            "lyrics": lyrics or "",
            "query": query,
        }
        pd.DataFrame([row_dict]).to_csv(
            str(csv_path),
            mode="a" if exists else "w",
            index=False,
            encoding="utf-8",
            header=not exists,
        )
        print(f"[MELON] Appended row to CSV: {csv_path}")
        print(f"[RESULT][MELON] title='{title}' singer='{singer}' csv='{csv_path}' lyrics_len={len(lyrics) if lyrics else 0}")

        return lyrics
    except Exception as e:
        print(f"[MELON][ERROR] {e}")
        return None
    finally:
        try:
            if driver is not None:
                driver.quit()
        except Exception:
            pass


def get_lyrics_csv_path() -> str:
    """Return the target CSV path for saving lyrics (UTF-8)."""
    return SONGS_OUT_NEW_CSV


