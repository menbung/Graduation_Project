from pathlib import Path
from typing import Optional
from config import MP3_OUTPUT_DIR  # type: ignore


def download_mp3_from_youtube(query: str, output_dir: Optional[str] = None) -> str:
    """
    Search YouTube for the query (via Selenium), download the first result's
    audio as MP3 using yt_dlp, and return the directory path where the MP3
    was saved.

    Requirements:
      - selenium + ChromeDriver
      - yt_dlp
      - ffmpeg (available in PATH for audio extraction)
    """
    print(f"[YT] Start download. query='{query}'")
    try:
        import yt_dlp  # type: ignore
    except Exception as e:
        raise RuntimeError("yt_dlp is required to download audio from YouTube. Install with: pip install yt-dlp") from e

    # Prepare output directory
    out_dir = Path(output_dir or MP3_OUTPUT_DIR).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[YT] Output directory: {out_dir}")

    # Try Selenium-driven search to get the first video URL
    video_url = None
    try:
        from selenium import webdriver  # type: ignore
        from selenium.webdriver.chrome.options import Options  # type: ignore
        from selenium.webdriver.common.by import By  # type: ignore
        from selenium.webdriver.common.keys import Keys  # type: ignore
        from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
        from selenium.webdriver.support import expected_conditions as EC  # type: ignore
        import time, os, re

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.get("https://www.youtube.com/")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "search_query")))

            box = driver.find_element(By.NAME, "search_query")
            box.clear()
            box.send_keys(query)
            box.send_keys(Keys.RETURN)
            print("[YT] Submitted YouTube search.")

            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.ID, "video-title"))
            )
            videos = driver.find_elements(By.ID, "video-title")
            for v in videos:
                href = v.get_attribute("href")
                if href:
                    video_url = href
                    break
            if not video_url:
                raise RuntimeError("No video URL found from search results")
            # Sanitize playlist params; keep only watch?v=VIDEOID if present
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(video_url)
                qs = parse_qs(parsed.query)
                vid = qs.get('v', [None])[0]
                if vid:
                    video_url = f"https://www.youtube.com/watch?v={vid}"
            except Exception:
                pass
            print(f"[YT] Found video: {video_url}")
        finally:
            try:
                if driver is not None:
                    driver.quit()
            except Exception:
                pass
    except Exception as e:
        print(f"[YT][WARN] Selenium path failed: {e}. Falling back to ytsearch.")

    # Configure yt_dlp and download
    import os, re
    safe_query = re.sub(r'[\\/:*?"<>|]', '_', query)
    ydl_opts = {
        # Prefer m4a (mp4a) first, then bestaudio
        'format': 'bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(str(out_dir), f'{safe_query}.%(ext)s'),
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
        'retries': 3,
        'fragment_retries': 3,
        'concurrent_fragment_downloads': 1,
        'nocheckcertificate': True,
    }
    # Add cookiefile if present (optional)
    cookie_path = Path('cookies.txt')
    if cookie_path.exists():
        ydl_opts['cookiefile'] = str(cookie_path)

    print("[YT] Downloading audio with yt_dlp...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            target = video_url or f"ytsearch1:{query}"
            ydl.download([target])
        final_mp3 = Path(out_dir) / f"{safe_query}.mp3"
        print(f"[YT] Download complete. dir='{out_dir}'")
        print(f"[RESULT][YT] saved='{final_mp3}' exists={final_mp3.exists()}")
        return str(out_dir)
    except Exception as e:
        print(f"[YT][ERROR] Download failed: {e}")
        # Diagnostic: list available formats for this video
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                target = video_url or f"ytsearch1:{query}"
                info = ydl.extract_info(target, download=False)
                fmts = info.get('formats', []) if isinstance(info, dict) else []
                exts = sorted({f.get('ext') for f in fmts if f.get('ext')})
                acodecs = sorted({f.get('acodec') for f in fmts if f.get('acodec')})
                print(f"[YT][DIAG] available extensions={exts}")
                print(f"[YT][DIAG] available acodecs={acodecs}")
        except Exception as e2:
            print(f"[YT][DIAG][ERROR] {e2}")
        raise
