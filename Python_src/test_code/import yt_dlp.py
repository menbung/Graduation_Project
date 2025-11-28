import yt_dlp
from pathlib import Path

VIDEO_URL = "https://youtu.be/08h8u8Z9iJQ?si=-V4KbROOfnKKNgA6"
OUT_DIR = Path("tmp_download")
OUT_DIR.mkdir(exist_ok=True)

def download_video(url: str) -> None:
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(OUT_DIR / "test_video.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        print("✅ download complete:", OUT_DIR)
    except Exception as exc:
        print("❌ download failed:", exc)
        print("\n[FORMAT LIST]")
        ydl = yt_dlp.YoutubeDL({"listformats": True})
        ydl.download([url])

if __name__ == "__main__":
    download_video(VIDEO_URL)