import joblib
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any
from pathlib import Path

class KNNModel:
    def __init__(self, n_neighbors=5):
        self.model = KNeighborsClassifier(n_neighbors=n_neighbors)

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def save(self, path: str):
        joblib.dump(self.model, path)

    def load(self, path: str):
        self.model = joblib.load(path)

def _parse_vector_cell(cell: Any) -> np.ndarray | None:
    if cell is None:
        return None
    try:
        # Try JSON-like list
        import ast
        v = ast.literal_eval(cell) if isinstance(cell, str) else cell
        arr = np.asarray(v, dtype=np.float32)
        if arr.ndim == 1 and arr.size > 0:
            return arr
    except Exception:
        pass
    try:
        # Try comma- or space-separated string
        if isinstance(cell, str):
            tokens = [t for t in cell.replace(",", " ").split() if t]
            arr = np.asarray([float(t) for t in tokens], dtype=np.float32)
            if arr.ndim == 1 and arr.size > 0:
                return arr
    except Exception:
        pass
    return None

def _build_feature(row: pd.Series, vector_cols: List[str]) -> np.ndarray | None:
    parts: List[np.ndarray] = []
    for col in vector_cols:
        if col not in row:
            return None
        vec = _parse_vector_cell(row[col])
        if vec is None:
            return None
        parts.append(vec)
    try:
        return np.concatenate(parts, axis=0).astype(np.float32)
    except Exception:
        return None

def _load_dataframe(csv_path: str) -> pd.DataFrame:
    return pd.read_csv(csv_path, encoding="utf-8-sig")

def _format_title(row: pd.Series) -> str:
    title = str(row.get("title", "")).strip()
    singer = str(row.get("singer", "")).strip()
    if singer and title:
        return f"{singer} - {title}"
    return title or singer or ""

def _extract_styles(row: pd.Series) -> List[str]:
    styles: List[str] = []
    for col in ("style_first", "style_second", "style_third"):
        val = str(row.get(col, "")).strip()
        if val:
            styles.append(val)
    return styles

def _extract_genres(row: pd.Series) -> List[str]:
    raw = str(row.get("genre_tags", "")).strip()
    if not raw:
        return []
    # Expecting comma-separated tags
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts

def _fit_neighbors(features: List[np.ndarray], metric: str = "cosine") -> NearestNeighbors:
    X = np.vstack(features).astype(np.float32)
    nn = NearestNeighbors(metric=metric)
    nn.fit(X)
    return nn

def _nearest_for_seed(
    seed_global_idx: int,
    global_indices: List[int],
    features: List[np.ndarray],
    df: pd.DataFrame,
    nn: NearestNeighbors,
    k_neighbors: int,
) -> Tuple[List[int], List[str]]:
    # Map seed global index to feature row index
    try:
        seed_local = global_indices.index(seed_global_idx)
    except ValueError:
        return [], []
    X = np.vstack(features).astype(np.float32)
    distances, indices = nn.kneighbors(X[seed_local : seed_local + 1], n_neighbors=min(k_neighbors + 1, len(global_indices)))
    idxs = indices[0].tolist()
    # Drop self if present
    filtered = [i for i in idxs if i != seed_local]
    # Map back to global indices and titles
    neighbor_global = [global_indices[i] for i in filtered]
    neighbor_titles = [_format_title(df.iloc[g]) for g in neighbor_global]
    return neighbor_global, neighbor_titles

def _aggregate_top(items: List[List[str]], top_n: int) -> List[str]:
    from collections import Counter
    counter: Counter = Counter()
    for lst in items:
        for it in lst:
            counter[it] += 1
    return [k for k, _ in counter.most_common(top_n)]

def recommend_from_csv_with_indices(
    csv_path: str,
    a: int,
    b: int,
    c: int,
    k_neighbors: int = 3,
    per_seed_top: int = 3,
    final_top: int = 3,
    vector_cols: List[str] | None = None,
) -> Dict[str, Any]:
    if vector_cols is None:
        vector_cols = ["genre_vector"]
    df = _load_dataframe(csv_path)
    features: List[np.ndarray] = []
    global_indices: List[int] = []
    for i, row in df.iterrows():
        feat = _build_feature(row, vector_cols)
        if feat is not None:
            features.append(feat)
            global_indices.append(i)
    if not features:
        return {"error": "No valid feature rows"}
    nn = _fit_neighbors(features, metric="cosine")
    seeds = [a, b, c]
    per_seed_neighbors: List[List[int]] = []
    per_seed_neighbor_titles: List[List[str]] = []
    per_seed_top_labels: List[List[str]] = []
    per_seed_top_genres: List[List[str]] = []
    seed_titles: List[str] = []
    for s in seeds:
        if 0 <= s < len(df):
            seed_titles.append(_format_title(df.iloc[s]))
        else:
            seed_titles.append("")
        neighbor_idx, neighbor_titles = _nearest_for_seed(s, global_indices, features, df, nn, k_neighbors)
        per_seed_neighbors.append(neighbor_idx[:per_seed_top])
        per_seed_neighbor_titles.append(neighbor_titles[:per_seed_top])
        # Aggregate styles/genres among per-seed neighbors
        styles_acc: List[str] = []
        genres_acc: List[str] = []
        for gi in neighbor_idx[:per_seed_top]:
            styles_acc.extend(_extract_styles(df.iloc[gi]))
            genres_acc.extend(_extract_genres(df.iloc[gi]))
        per_seed_top_labels.append(_aggregate_top([styles_acc], per_seed_top))
        if genres_acc:
            per_seed_top_genres.append(_aggregate_top([genres_acc], per_seed_top))
        else:
            per_seed_top_genres.append([])
    # Final aggregation over all neighbors from 3 seeds
    all_style_labels: List[str] = []
    all_genre_labels: List[str] = []
    for lst in per_seed_neighbors:
        for gi in lst:
            all_style_labels.extend(_extract_styles(df.iloc[gi]))
            all_genre_labels.extend(_extract_genres(df.iloc[gi]))
    final_top_labels = _aggregate_top([all_style_labels], final_top)
    final_top_genres = _aggregate_top([all_genre_labels], final_top) if all_genre_labels else []
    return {
        "model_id": 1,
        "seed_titles": seed_titles,
        "per_seed_neighbor_titles": per_seed_neighbor_titles,
        "per_seed_top_labels": per_seed_top_labels,
        "per_seed_top_genres": per_seed_top_genres,
        "final_top_labels": final_top_labels,
        "final_top_genres": final_top_genres,
    }

def recommend_with_config_seeds(
    seeds: List[int],
    k_neighbors: int = 3,
    per_seed_top: int = 3,
    final_top: int = 3,
    vector_cols: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Prefer a pre-trained bundle at models/knn_model.joblib if present.
    Fallback to CSV-based neighbors otherwise.
    """
    if len(seeds) != 3:
        return {"error": "seeds must have length 3"}

    # Try pretrained bundle
    bundle_path = Path(__file__).resolve().parent / "knn_model.joblib"
    if bundle_path.exists():
        try:
            obj = joblib.load(str(bundle_path))
            # Expecting a dict bundle with at least 'matrix' and 'valid_mask'
            if isinstance(obj, dict) and "matrix" in obj:
                M_all = np.asarray(obj["matrix"], dtype=np.float32)
                valid_mask = np.asarray(obj.get("valid_mask", np.ones(len(M_all), dtype=bool)))
                if valid_mask.dtype != bool:
                    valid_mask = valid_mask.astype(bool)
                valid_indices = np.where(valid_mask)[0]
                if valid_indices.size == 0:
                    raise ValueError("valid_mask has no True entries")
                M_valid = M_all[valid_mask]
                # Use provided nn if available, else fit a new one
                nn = obj.get("nn", None)
                if nn is None or not hasattr(nn, "kneighbors"):
                    nn = _fit_neighbors([x for x in M_valid], metric="cosine")

                # Build mapping from original index -> local(valid) index
                orig_to_local = -np.ones(len(valid_mask), dtype=int)
                orig_to_local[valid_indices] = np.arange(len(valid_indices))

                # Resolve CSV path relative to project root (Python_src)
                project_root = Path(__file__).resolve().parents[1]
                csv_path = project_root / "data" / "songs_out_final.csv"
                df = _load_dataframe(str(csv_path))

                per_seed_neighbors: List[List[int]] = []
                per_seed_neighbor_titles: List[List[str]] = []
                per_seed_top_labels: List[List[str]] = []
                per_seed_top_genres: List[List[str]] = []
                seed_titles: List[str] = []

                for s in seeds:
                    if 0 <= int(s) < len(df):
                        seed_titles.append(_format_title(df.iloc[int(s)]))
                    else:
                        seed_titles.append("")
                    local_idx = orig_to_local[int(s)] if 0 <= int(s) < len(orig_to_local) else -1
                    if local_idx < 0:
                        per_seed_neighbors.append([])
                        per_seed_neighbor_titles.append([])
                        per_seed_top_labels.append([])
                        per_seed_top_genres.append([])
                        continue
                    # Query neighbors on the precomputed space
                    distances, indices = nn.kneighbors(M_valid[local_idx : local_idx + 1], n_neighbors=min(int(k_neighbors) + 1, len(M_valid)))
                    nbr_local = [i for i in indices[0].tolist() if i != local_idx]
                    nbr_orig = [int(valid_indices[i]) for i in nbr_local][:int(per_seed_top)]
                    per_seed_neighbors.append(nbr_orig)
                    per_seed_neighbor_titles.append([_format_title(df.iloc[i]) for i in nbr_orig])
                    styles_acc: List[str] = []
                    genres_acc: List[str] = []
                    for gi in nbr_orig:
                        styles_acc.extend(_extract_styles(df.iloc[gi]))
                        genres_acc.extend(_extract_genres(df.iloc[gi]))
                    per_seed_top_labels.append(_aggregate_top([styles_acc], int(per_seed_top)))
                    per_seed_top_genres.append(_aggregate_top([genres_acc], int(per_seed_top)) if genres_acc else [])

                # Final aggregation
                all_style_labels: List[str] = []
                all_genre_labels: List[str] = []
                for lst in per_seed_neighbors:
                    for gi in lst:
                        all_style_labels.extend(_extract_styles(df.iloc[gi]))
                        all_genre_labels.extend(_extract_genres(df.iloc[gi]))
                final_top_labels = _aggregate_top([all_style_labels], int(final_top))
                final_top_genres = _aggregate_top([all_genre_labels], int(final_top)) if all_genre_labels else []

                return {
                    "model_id": 1,
                    "seed_titles": seed_titles,
                    "per_seed_neighbor_titles": per_seed_neighbor_titles,
                    "per_seed_top_labels": per_seed_top_labels,
                    "per_seed_top_genres": per_seed_top_genres,
                    "final_top_labels": final_top_labels,
                    "final_top_genres": final_top_genres,
                    "used_pretrained": True,
                }
        except Exception:
            # Fall back to CSV approach if bundle is incompatible
            pass

    # Fallback to CSV-based recommendation (resolve project root)
    project_root = Path(__file__).resolve().parents[1]
    csv_path = project_root / "data" / "songs_out_final.csv"
    return recommend_from_csv_with_indices(
        csv_path=str(csv_path),
        a=int(seeds[0]),
        b=int(seeds[1]),
        c=int(seeds[2]),
        k_neighbors=int(k_neighbors),
        per_seed_top=int(per_seed_top),
        final_top=int(final_top),
        vector_cols=vector_cols or ["genre_vector", "mood_vector", "texture_vector"],
    )
