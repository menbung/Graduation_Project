from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, List, Dict

import torch
from PIL import Image

try:
    from transformers import CLIPModel, CLIPProcessor
except Exception:  # transformers가 없는 환경에서도 import 시점 오류 방지
    CLIPModel = None  # type: ignore
    CLIPProcessor = None  # type: ignore


_GLOBAL_MODEL: Optional["CLIPModel"] = None
_GLOBAL_PROCESSOR: Optional["CLIPProcessor"] = None
_GLOBAL_DEVICE: Optional[str] = None


def _default_model_dir() -> Path:
    """Resolve default local directory for the finetuned fashion-clip model.

    Expects a Hugging Face-style saved directory placed at:
      Python_src/feature/fashion_clip_model/fashionclip-ft
    """
    return Path(__file__).resolve().parent / "fashion_clip_model" / "fashionclip-ft"


def _resolve_path(model_dir: Optional[str]) -> Path:
    if model_dir is None:
        return _default_model_dir()
    p = Path(model_dir)
    if p.is_absolute():
        return p
    # Try CWD, then path relative to this file
    p_cwd = Path.cwd() / p
    if p_cwd.exists():
        return p_cwd
    return Path(__file__).resolve().parent / p


def load_fashionclip(
    model_dir: Optional[str] = None,
    device: Optional[str] = None,
    use_half: Optional[bool] = None,
) -> Tuple["CLIPModel", "CLIPProcessor", str]:
    """Load the finetuned Fashion-CLIP model and processor.

    - model_dir: path to HF save directory (default: feature/fashion_clip_model/fashionclip-ft)
    - device: "cuda", "cpu" (default: auto)
    - use_half: if True and device supports, load with float16
    """
    global _GLOBAL_MODEL, _GLOBAL_PROCESSOR, _GLOBAL_DEVICE

    if CLIPModel is None or CLIPProcessor is None:
        raise ImportError("transformers 패키지가 필요합니다. pip install transformers")

    resolved = _resolve_path(model_dir)
    if not resolved.exists():
        raise FileNotFoundError(f"모델 디렉터리를 찾을 수 없습니다: {resolved}")

    # If config.json is missing directly, but exists in a single nested subfolder
    if not (resolved / "config.json").exists():
        try:
            subdirs = [d for d in resolved.iterdir() if d.is_dir()]
            for d in subdirs:
                if (d / "config.json").exists():
                    resolved = d
                    break
        except Exception:
            pass

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if use_half is None:
        use_half = (device == "cuda")

    torch_dtype = "float16" if use_half else "float32"

    model = CLIPModel.from_pretrained(str(resolved), torch_dtype=torch_dtype)
    processor = CLIPProcessor.from_pretrained(str(resolved), use_fast=True)

    model = model.to(device)
    model.eval()

    _GLOBAL_MODEL = model
    _GLOBAL_PROCESSOR = processor
    _GLOBAL_DEVICE = device
    return model, processor, device


def _ensure_loaded(model_dir: Optional[str] = None) -> Tuple["CLIPModel", "CLIPProcessor", str]:
    global _GLOBAL_MODEL, _GLOBAL_PROCESSOR, _GLOBAL_DEVICE
    if _GLOBAL_MODEL is not None and _GLOBAL_PROCESSOR is not None and _GLOBAL_DEVICE is not None:
        return _GLOBAL_MODEL, _GLOBAL_PROCESSOR, _GLOBAL_DEVICE
    return load_fashionclip(model_dir=model_dir)


def image_to_embedding(image_path: str, model_dir: Optional[str] = None) -> List[float]:
    """Encode an image file into a CLIP embedding (L2-normalized).

    Returns a Python list[float] for easy JSON serialization.
    """
    model, processor, device = _ensure_loaded(model_dir)
    img = Image.open(image_path).convert("RGB")
    inputs = processor(images=img, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        feats = model.get_image_features(**inputs)
        feats = torch.nn.functional.normalize(feats, dim=-1)
    return feats[0].detach().cpu().float().tolist()


def text_to_embedding(text: str, model_dir: Optional[str] = None) -> List[float]:
    """Encode a text string into a CLIP embedding (L2-normalized)."""
    model, processor, device = _ensure_loaded(model_dir)
    inputs = processor(
        text=[text],
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=77,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        feats = model.get_text_features(**inputs)
        feats = torch.nn.functional.normalize(feats, dim=-1)
    return feats[0].detach().cpu().float().tolist()


__all__ = [
    "load_fashionclip",
    "image_to_embedding",
    "text_to_embedding",
]


# ----------------------------------------------------
# Caption → Top-K images retrieval from data/cloth tree
# ----------------------------------------------------
def rank_images_for_caption(
    caption: str,
    root_dir: Optional[str] = None,
    top_k: int = 20,
    batch_size: int = 16,
    model_dir: Optional[str] = None,
    scan_limit: Optional[int] = None,
    progress_every: int = 100,
) -> List[Tuple[str, float]]:
    """Return top_k image paths under data/cloth for a given caption.

    - root_dir: if None, defaults to Python_src/data/cloth
    - returns list of (filepath, cosine_similarity)
    """
    model, processor, device = _ensure_loaded(model_dir)

    root = Path(root_dir) if root_dir is not None else (Path(__file__).resolve().parents[1] / "data" / "cloth")
    if not root.exists():
        raise FileNotFoundError(f"image root not found: {root}")

    # Collect all image paths
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    image_paths: List[Path] = [p for p in root.rglob("*") if p.suffix.lower() in exts]
    if scan_limit is not None and scan_limit > 0:
        image_paths = image_paths[:scan_limit]
    if not image_paths:
        return []

    # Text embedding (normalized)
    txt_vec = torch.tensor(text_to_embedding(caption, model_dir=model_dir), device=device).unsqueeze(0)

    scores: List[Tuple[str, float]] = []
    model.eval()
    with torch.no_grad():
        # Batch images for efficiency
        total = len(image_paths)
        for i in range(0, total, max(1, batch_size)):
            batch_paths = image_paths[i:i + batch_size]
            imgs: List[Image.Image] = []
            valid_idx: List[int] = []
            for j, path in enumerate(batch_paths):
                try:
                    imgs.append(Image.open(path).convert("RGB"))
                    valid_idx.append(j)
                except Exception:
                    continue
            if not imgs:
                continue
            inputs = processor(images=imgs, return_tensors="pt", padding=True)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            img_feats = model.get_image_features(**inputs)
            img_feats = torch.nn.functional.normalize(img_feats, dim=-1)
            sim = (img_feats @ txt_vec.T).squeeze(1)  # cosine since normalized
            for j, s in zip(valid_idx, sim.tolist()):
                scores.append((str(batch_paths[j]), float(s)))
            if progress_every > 0 and ((i + len(batch_paths)) % progress_every == 0 or (i + len(batch_paths)) >= total):
                print(f"[Fashion-CLIP] processed {min(i + len(batch_paths), total)}/{total} images")

    # Top-K by similarity
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:max(0, top_k)]


# -----------------------------
# Embedding index build & query
# -----------------------------
def build_image_embedding_index(
    root_dir: Optional[str] = None,
    out_path: Optional[str] = None,
    model_dir: Optional[str] = None,
    batch_size: int = 32,
) -> str:
    """Precompute image embeddings and save to a .pt file containing:
      {
        'paths': List[str],
        'features': torch.FloatTensor [N, D] (L2-normalized)
      }

    Returns the saved path.
    """
    model, processor, device = _ensure_loaded(model_dir)
    root = Path(root_dir) if root_dir is not None else (Path(__file__).resolve().parents[1] / "data" / "cloth")
    if not root.exists():
        raise FileNotFoundError(f"image root not found: {root}")
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    image_paths: List[Path] = [p for p in root.rglob("*") if p.suffix.lower() in exts]
    if not image_paths:
        raise ValueError("no images found")

    feats_list: List[torch.Tensor] = []
    str_paths: List[str] = []
    with torch.no_grad():
        for i in range(0, len(image_paths), max(1, batch_size)):
            batch_paths = image_paths[i:i + batch_size]
            imgs: List[Image.Image] = []
            valid_idx: List[int] = []
            for j, path in enumerate(batch_paths):
                try:
                    imgs.append(Image.open(path).convert("RGB"))
                    valid_idx.append(j)
                except Exception:
                    continue
            if not imgs:
                continue
            inputs = processor(images=imgs, return_tensors="pt", padding=True)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            img_feats = model.get_image_features(**inputs)
            img_feats = torch.nn.functional.normalize(img_feats, dim=-1)
            feats_list.append(img_feats.detach().cpu())
            for j in valid_idx:
                str_paths.append(str(batch_paths[j]))
            if (i + len(batch_paths)) % 200 == 0 or (i + len(batch_paths)) >= len(image_paths):
                print(f"[Index] processed {min(i + len(batch_paths), len(image_paths))}/{len(image_paths)} images")

    features = torch.cat(feats_list, dim=0) if feats_list else torch.empty((0, 0))
    if features.numel() == 0:
        raise ValueError("failed to compute any features")

    payload: Dict[str, object] = {"paths": str_paths, "features": features}
    if out_path is None:
        out_path = str((Path(__file__).resolve().parent / "fashion_clip_model" / "image_index.pt"))
    torch.save(payload, out_path)
    print(f"[Index] saved: {out_path}  (N={features.shape[0]}, D={features.shape[1]})")
    return out_path


def rank_with_prebuilt_index(
    caption: str,
    index_path: str,
    top_k: int = 20,
    model_dir: Optional[str] = None,
) -> List[Tuple[str, float]]:
    """Query top_k using a prebuilt index file produced by build_image_embedding_index."""
    _model, _processor, device = _ensure_loaded(model_dir)
    payload = torch.load(index_path, map_location="cpu")
    paths: List[str] = payload["paths"]
    feats: torch.Tensor = payload["features"]  # [N, D], already normalized
    if not isinstance(paths, list) or not isinstance(feats, torch.Tensor):
        raise ValueError("invalid index payload")
    if feats.ndim != 2 or len(paths) != feats.shape[0]:
        raise ValueError("index shapes mismatch")

    txt = torch.tensor(text_to_embedding(caption, model_dir=model_dir), dtype=feats.dtype)
    txt = txt.unsqueeze(0)  # [1, D]
    sim = (feats @ txt.T).squeeze(1)
    topk = torch.topk(sim, k=min(top_k, sim.shape[0]))
    result: List[Tuple[str, float]] = [(paths[int(i)], float(s)) for s, i in zip(topk.values.tolist(), topk.indices.tolist())]
    return result

