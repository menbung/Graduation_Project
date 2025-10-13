from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
import os

# Fixed CSV path (project-relative by default), override via env CSV_SONGS_PATH if needed
_DEFAULT_CSV = Path(__file__).resolve().parent / "data" / "songs_out_final.csv"
CSV_SONGS_PATH: str = os.getenv("CSV_SONGS_PATH", str(_DEFAULT_CSV))
