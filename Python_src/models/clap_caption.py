from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
import torch
import torch.nn.functional as F
import librosa

try:
    from laion_clap import CLAP_Module  # type: ignore
except Exception as e:  # pragma: no cover
    CLAP_Module = None  # type: ignore


_clap_model = None
_tag_prompts: List[str] | None = None
_tag_category_map: Dict[str, str] | None = None
_tag_embeddings = None


def _get_clap_model():
    global _clap_model
    if _clap_model is not None:
        return _clap_model
    if CLAP_Module is None:
        raise RuntimeError("laion_clap is not installed. Install with: pip install laion-clap")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = CLAP_Module(enable_fusion=False, device=device)
    model.load_ckpt()
    _clap_model = model
    return _clap_model


def _load_audio_tensor(path: str, target_sr: int = 48000) -> torch.Tensor:
    audio_data, _sr = librosa.load(path, sr=target_sr)
    audio_data = audio_data.reshape(1, -1)

    def int16_to_float32(x: np.ndarray) -> np.ndarray:
        return (x / 32767.0).astype(np.float32)

    def float32_to_int16(x: np.ndarray) -> np.ndarray:
        x = np.clip(x, a_min=-1.0, a_max=1.0)
        return (x * 32767.0).astype(np.int16)

    audio_quantized = float32_to_int16(audio_data)
    audio_float = int16_to_float32(audio_quantized)
    return torch.from_numpy(audio_float).float()


def _find_first_mp3(audio_dir: str) -> str | None:
    p = Path(audio_dir)
    if not p.exists():
        return None
    for ext in ("*.mp3", "*.MP3"):
        files = list(p.glob(ext))
        if files:
            return str(files[0])
    return None


def _get_tag_vocab_and_embeddings() -> Tuple[List[str], Dict[str, str], torch.Tensor]:
    """
    Build and cache tag prompts (genre/mood/texture) and their embeddings.
    Returns (tag_prompts, tag_category_map, tag_embeddings[T, D]).
    """
    global _tag_prompts, _tag_category_map, _tag_embeddings
    if _tag_prompts is not None and _tag_category_map is not None and _tag_embeddings is not None:
        return _tag_prompts, _tag_category_map, _tag_embeddings

    # Tag vocab
    genre_tags = [
        "Hip-Hop", "Rap", "Rock", "Alternative Rock", "Punk",
        "Pop", "Indie Pop", "R&B", "Soul", "Jazz", "Classical",
        "Electronic", "Ambient", "Folk", "Acoustic",
        "Reggae", "Latin", "Country", "Blues", "Experimental",
    ]
    mood_tags = [
        "Happy", "Sad", "Energetic", "Chill", "Relaxed", "Dark", "Romantic",
        "Uplifting", "Melancholic", "Angry", "Nostalgic", "Dreamy",
        "Hypnotic", "Mysterious", "Playful", "Aggressive",
    ]
    texture_tags = [
        "Lo-fi", "Clean", "Distorted", "Warm", "Bright", "Harsh", "Smooth",
        "Gritty", "Metallic", "Acoustic", "Synthetic", "Dry", "Wet",
        "Punchy", "Muffled",
    ]

    all_tags = genre_tags + mood_tags + texture_tags
    tag_category_map: Dict[str, str] = {}
    for t in genre_tags:
        tag_category_map[t] = "genre"
    for t in mood_tags:
        tag_category_map[t] = "mood"
    for t in texture_tags:
        tag_category_map[t] = "texture"

    tag_prompts = [f"A {tag} music" for tag in all_tags]

    model = _get_clap_model()
    emb = model.get_text_embedding(tag_prompts, use_tensor=True)
    if not torch.is_tensor(emb):
        emb = torch.as_tensor(emb)
    _tag_prompts = tag_prompts
    _tag_category_map = tag_category_map
    _tag_embeddings = emb.float()
    return _tag_prompts, _tag_category_map, _tag_embeddings


def _rank_lyrics_lines_by_audio_similarity(
    audio_emb: torch.Tensor,
    lines: List[str],
    top_n: int,
) -> List[str]:
    model = _get_clap_model()
    text_embs = model.get_text_embedding(lines, use_tensor=True)  # [N, D]
    if not torch.is_tensor(text_embs):
        text_embs = torch.as_tensor(text_embs)
    text_embs = text_embs.float()

    # L2 normalize, then compute dot-product similarity
    audio_norm = F.normalize(audio_emb, p=2, dim=-1)  # [1, D]
    text_norm = F.normalize(text_embs, p=2, dim=-1)   # [N, D]
    sims = torch.matmul(audio_norm, text_norm.T).squeeze(0)  # [N]

    sorted_indices = torch.argsort(sims, descending=True)
    top_lines: List[str] = []
    seen: set[str] = set()
    for idx in sorted_indices.tolist():
        line = lines[idx]
        if line in seen:
            continue
        top_lines.append(line)
        seen.add(line)
        if len(top_lines) >= top_n:
            break
    return top_lines


def generate_caption_with_clap(audio_dir: str, lyrics_text: str, top_n: int = 2) -> str:
    """
    Produce a caption by selecting the top-N lyric lines most similar to the
    audio, using a CLAP model.

    Args:
        audio_dir: Directory containing at least one MP3 file.
        lyrics_text: Raw lyrics string (newline-separated).
        top_n: Number of best-matching lines to include in the caption.

    Returns:
        caption string. If anything fails, returns an empty string.
    """
    try:
        print(f"[CLAP] Start caption. audio_dir='{audio_dir}'")
        mp3_path = _find_first_mp3(audio_dir)
        if not mp3_path:
            print("[CLAP][WARN] No MP3 found.")
            return ""

        lines = [line.strip() for line in (lyrics_text or "").splitlines() if line.strip()]
        if not lines:
            print("[CLAP][WARN] No non-empty lyrics lines.")
            return ""

        model = _get_clap_model()
        audio_tensor = _load_audio_tensor(mp3_path)
        audio_emb = model.get_audio_embedding_from_data(x=audio_tensor, use_tensor=True)  # [1, D]
        if not torch.is_tensor(audio_emb):
            audio_emb = torch.as_tensor(audio_emb)
        audio_emb = audio_emb.float()

        # 1) Summary lyrics from top-N matching lines
        top_lines = _rank_lyrics_lines_by_audio_similarity(audio_emb, lines, top_n=top_n)
        lyrics_summary = " ".join(top_lines).strip()
        print(f"[CLAP] Summary lines count={len(top_lines)}")

        # 2) Predict mood (and optionally genre/texture) using tag embeddings
        tag_prompts, tag_category_map, tag_embs = _get_tag_vocab_and_embeddings()
        # Normalize
        a_norm = F.normalize(audio_emb, p=2, dim=-1)  # [1, D]
        t_norm = F.normalize(tag_embs, p=2, dim=-1)  # [T, D]
        sims = torch.matmul(a_norm, t_norm.T).squeeze(0)  # [T]

        # Group by category and pick top-k
        scores_by_cat: Dict[str, List[Tuple[str, float]]] = {"genre": [], "mood": [], "texture": []}
        for idx, score in enumerate(sims.tolist()):
            tag_sentence = tag_prompts[idx]
            # Extract the raw tag back from the prompt
            # Prompt format: "A {tag} music" -> recover {tag}
            if tag_sentence.startswith("A ") and tag_sentence.endswith(" music"):
                tag = tag_sentence[2:-6].strip()
            else:
                tag = tag_sentence
            cat = tag_category_map.get(tag, "mood")
            if cat not in scores_by_cat:
                scores_by_cat[cat] = []
            scores_by_cat[cat].append((tag, score))

        def _top_k(items: List[Tuple[str, float]], k: int) -> List[str]:
            return [t for t, _ in sorted(items, key=lambda x: x[1], reverse=True)[:k]]

        top_moods = _top_k(scores_by_cat.get("mood", []), 2)
        top_genres = _top_k(scores_by_cat.get("genre", []), 2)
        top_textures = _top_k(scores_by_cat.get("texture", []), 2)
        print(f"[CLAP] moods={top_moods} genres={top_genres} textures={top_textures}")

        # 3) Compose caption: summary lyrics + mood/genre/texture
        parts = [lyrics_summary]
        if top_moods:
            parts.append(f"mood: {', '.join(top_moods)}")
        if top_genres:
            parts.append(f"genre: {', '.join(top_genres)}")
        if top_textures:
            parts.append(f"texture: {', '.join(top_textures)}")
        caption = " | ".join([p for p in parts if p]).strip()
        print(f"[CLAP] Caption generated: {caption[:120]}{'...' if len(caption)>120 else ''}")
        print(f"[RESULT][CLAP] summary_len={len(lyrics_summary.split())} moods={top_moods} genres={top_genres} textures={top_textures}")
        return caption
    except Exception as e:
        print(f"[CLAP][ERROR] {e}")
        return ""

