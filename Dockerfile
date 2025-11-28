FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/Python_src

# System dependencies: ffmpeg (yt-dlp postprocess), chromium + chromedriver (Selenium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    chromium \
    chromium-driver \
    ca-certificates \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (torch installed separately for correct platform wheels)
COPY requirements.txt ./requirements.txt
RUN python -m pip install -U pip setuptools wheel \
    && python -m pip install -r requirements.txt \
    && python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy project sources
COPY Python_src ./Python_src

# Create expected data/model directories (avoid runtime mkdir races)
RUN mkdir -p Python_src/data/new_songs/mp3 \
    && mkdir -p Python_src/data/songs_out \
    && mkdir -p Python_src/feature/fashion_clip_model

# Expose API port
EXPOSE 8000

# Default: run FastAPI server. Respect Cloud Run $PORT (fallback 8080 for cloud, 8000 local)
CMD ["sh", "-c", "uvicorn Python_src.api.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
