import os
import csv
from pathlib import Path

# 기본 경로 설정 (필요 시 수정)
BASE_DIR = Path(r"C:\Users\user\G_project_2\Python_src\data\cloth")
OUTPUT_CSV = Path(r"C:\Users\user\G_project_2\Python_src\data\cloth_filenames.csv")

# 수집 대상 파일 확장자 (의류 이미지 중심)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

# 대상 하위 폴더(스타일) 화이트리스트
ALLOWED_STYLES = {
    "나시", "나이키", "레트로", "로맨틱", "미니멀", "비즈니스캐주얼", "빈티지",
    "섹시", "스트릿", "스포티", "시크", "언더아머", "오피스", "캐주얼", "클래식", "펑크",
}


def list_files(base_dir: Path):
    """
    base_dir 하위의 허용된 스타일 폴더만 순회하며 이미지 파일 목록을 생성합니다.
    반환: 리스트[tuple(style, filename)]
    """
    items = []
    # 허용된 스타일 폴더만 대상으로 걷기
    for style in sorted(ALLOWED_STYLES):
        style_dir = base_dir / style
        if not style_dir.exists():
            continue
        for root, _, files in os.walk(style_dir):
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext not in IMAGE_EXTS:
                    continue
                items.append((style, fname))
    return items


def save_csv(rows, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        # 헤더: 1번열 번호, 2번열 스타일, 3번열 파일명
        writer.writerow(["번호", "스타일", "파일명"])
        for idx, (style, filename) in enumerate(rows, start=1):
            writer.writerow([idx, style, filename])


def main():
    if not BASE_DIR.exists():
        raise FileNotFoundError(f"Base dir not found: {BASE_DIR}")
    rows = list_files(BASE_DIR)
    save_csv(rows, OUTPUT_CSV)
    print(f"✅ 총 {len(rows)}개 파일 기록 완료: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

