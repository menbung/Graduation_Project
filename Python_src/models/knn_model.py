import joblib
from sklearn.neighbors import KNeighborsClassifier
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from pathlib import Path
import os
import csv
import json
import re
from config import CSV_SONGS_PATH

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


class SavedKNNIndex:
    """Wrapper for a saved NearestNeighbors payload created in the notebook.

    The joblib payload is expected to contain keys:
      - 'nn_model': sklearn.neighbors.NearestNeighbors (fit on matrix[valid_mask])
      - 'matrix': numpy.ndarray of shape (num_rows, dim)
      - 'valid_mask': numpy.ndarray of shape (num_rows,) of bool
      - 'titles': List[str] of length num_rows
      - 'vector_col': str (optional)
    """

    def __init__(self, payload: Dict[str, Any]):
        self.nn_model = payload.get("nn_model")
        self.full_matrix: np.ndarray = payload.get("matrix")
        self.valid_mask: np.ndarray = payload.get("valid_mask")
        self.titles: List[str] = payload.get("titles")
        self.vector_column_name: Optional[str] = payload.get("vector_col")

        if self.nn_model is None or self.full_matrix is None or self.valid_mask is None or self.titles is None:
            raise ValueError("Invalid saved KNN payload: missing required keys")

        if not isinstance(self.full_matrix, np.ndarray) or not isinstance(self.valid_mask, np.ndarray):
            raise ValueError("'matrix' and 'valid_mask' must be numpy arrays")

        if self.full_matrix.shape[0] != self.valid_mask.shape[0] or self.full_matrix.shape[0] != len(self.titles):
            raise ValueError("Payload shape mismatch between matrix, valid_mask, and titles")

        # Indices in the original table corresponding to rows used to train nn_model
        self.valid_row_indices: np.ndarray = np.where(self.valid_mask)[0]

    @classmethod
    def _resolve_path(cls, path: Optional[str]) -> Path:
        if path is None:
            # default: file placed next to this module (Python_src/models/knn_model.joblib)
            return Path(__file__).resolve().parent / "knn_model.joblib"
        p = Path(path)
        if p.is_absolute():
            return p
        # Try current working directory first (useful for CLI/Colab runs)
        p_cwd = Path.cwd() / p
        if p_cwd.exists():
            return p_cwd
        # Fallback to path relative to this file's directory
        return (Path(__file__).resolve().parent / p)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "SavedKNNIndex":
        resolved = cls._resolve_path(path)
        payload = joblib.load(str(resolved))
        return cls(payload)

    @classmethod
    def load_default(cls) -> "SavedKNNIndex":
        """Load from models/knn_model.joblib next to this module."""
        return cls.load(None)

    def _ensure_dim(self, vector: np.ndarray) -> np.ndarray:
        if vector.ndim == 1:
            return vector.reshape(1, -1)
        return vector

    def kneighbors_for_vector(
        self,
        vector: np.ndarray,
        n_neighbors: int = 5,
        return_distance: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Query neighbors for an arbitrary feature vector.

        Returns (distances, row_indices, titles).
        row_indices are original CSV row indices.
        """
        query = self._ensure_dim(vector)
        distances, nn_indices = self.nn_model.kneighbors(query, n_neighbors=n_neighbors, return_distance=True)
        # Map from indices in the compact valid set back to original row indices
        row_indices = self.valid_row_indices[nn_indices[0]]
        titles = [self.titles[i] for i in row_indices]
        if return_distance:
            return distances[0], row_indices, titles
        return np.array([]), row_indices, titles

    def kneighbors_by_row_index(
        self,
        row_index: int,
        n_neighbors: int = 5,
        return_distance: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Query neighbors using an original CSV row index."""
        if row_index < 0 or row_index >= self.full_matrix.shape[0]:
            raise IndexError("row_index out of range")
        if not self.valid_mask[row_index]:
            raise ValueError("Row index is not valid in the saved KNN (vector missing or wrong dim)")
        # Position of this row inside the compact valid set
        valid_pos = int(np.where(self.valid_row_indices == row_index)[0][0])
        distances, nn_indices = self.nn_model.kneighbors(
            self.full_matrix[self.valid_mask][valid_pos].reshape(1, -1),
            n_neighbors=n_neighbors,
            return_distance=True,
        )
        neighbor_row_indices = self.valid_row_indices[nn_indices[0]]
        titles = [self.titles[i] for i in neighbor_row_indices]
        if return_distance:
            return distances[0], neighbor_row_indices, titles
        return np.array([]), neighbor_row_indices, titles

    def kneighbors_by_title(
        self,
        title: str,
        n_neighbors: int = 5,
        return_distance: bool = True,
        case_insensitive: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Query neighbors using an exact title match."""
        target = title if not case_insensitive else title.strip().lower()
        found_index: Optional[int] = None
        for i, t in enumerate(self.titles):
            if not isinstance(t, str):
                continue
            cand = t if not case_insensitive else t.strip().lower()
            if cand == target:
                found_index = i
                break
        if found_index is None:
            raise ValueError(f"Title not found: {title}")
        return self.kneighbors_by_row_index(found_index, n_neighbors=n_neighbors, return_distance=return_distance)


# -----------------------------
# CSV-based recommendation utils
# -----------------------------

def _find_col_idx(header: List[str], candidates: List[str]) -> Optional[int]:
    lower = [c.lower() if isinstance(c, str) else c for c in header]
    for cand in candidates:
        try:
            return lower.index(cand.lower())
        except ValueError:
            continue
    return None


def _find_col_indices(header: List[str], candidates: List[str]) -> List[int]:
    lower = [c.lower() if isinstance(c, str) else c for c in header]
    wanted = {c.lower() for c in candidates}
    indices: List[int] = []
    for i, name in enumerate(lower):
        if isinstance(name, str) and name in wanted:
            indices.append(i)
    return indices


def _parse_json_vector(cell: str) -> Optional[List[float]]:
    if not isinstance(cell, str) or not cell.strip():
        return None
    try:
        v = json.loads(cell)
        if isinstance(v, list) and all(isinstance(x, (int, float)) for x in v):
            return [float(x) for x in v]
    except Exception:
        return None
    return None


def _resolve_seed_to_index(seed: object, titles: List[str]) -> Optional[int]:
    try:
        idx = int(seed)
        if 0 <= idx < len(titles):
            return idx
        if 1 <= idx <= len(titles):
            return idx - 1
    except Exception:
        pass
    if isinstance(seed, str):
        target = seed.strip().lower()
        for i, t in enumerate(titles):
            if isinstance(t, str) and t.strip().lower() == target:
                return i
    return None


def recommend_by_knn_multi_vectors(
    csv_path: str,
    seeds: List[object],
    k_neighbors: int = 3,
    per_seed_top: int = 3,
    final_top: int = 3,
    vector_cols: Optional[List[str]] = None,
    label_col_candidates: Optional[List[str]] = None,
    title_col_candidates: Optional[List[str]] = None,
) -> Dict[str, object]:
    """Compute recommendations directly from a CSV using cosine similarity over vector columns.

    Returns dict with keys:
      - seed_titles
      - per_seed_top_labels
      - per_seed_top_genres
      - final_top_labels
      - final_top_genres
      - neighbors_indices
      - per_seed_neighbor_titles
    """
    if vector_cols is None:
        vector_cols = ["genre_vector", "mood_vector", "texture_vector"]
    if label_col_candidates is None:
        label_col_candidates = [
            "style_first", "style_second", "style_third",
            "outfit_style", "style", "clothes_style", "cloth_style",
            "패션", "스타일", "outfit",
        ]
    if title_col_candidates is None:
        title_col_candidates = ["title", "song", "name", "track", "곡명", "제목"]

    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        raise ValueError("빈 CSV")

    header = rows[0]
    data_rows = rows[1:]
    if not data_rows:
        raise ValueError("데이터 행이 없습니다")

    # column indices
    vec_indices: List[int] = []
    for col in vector_cols:
        idx = _find_col_idx(header, [col])
        if idx is not None:
            vec_indices.append(idx)
    if not vec_indices:
        raise ValueError(f"벡터 열을 찾을 수 없습니다: {vector_cols}")

    title_idx = _find_col_idx(header, title_col_candidates)
    titles = [r[title_idx] if (title_idx is not None and title_idx < len(r)) else str(i) for i, r in enumerate(data_rows)]

    label_indices = _find_col_indices(header, label_col_candidates)
    genre_idx_opt = _find_col_idx(header, ["genre_tags"])  # optional

    # build matrices
    matrices: List[np.ndarray] = []
    valids: List[np.ndarray] = []

    for vi in vec_indices:
        vectors: List[Optional[List[float]]] = []
        for r in data_rows:
            cell = r[vi] if vi < len(r) else ""
            vectors.append(_parse_json_vector(cell))
        dim = 0
        for v in vectors:
            if isinstance(v, list) and len(v) > 0:
                dim = len(v)
                break
        if dim == 0:
            continue
        M = np.zeros((len(vectors), dim), dtype=np.float32)
        valid = np.zeros((len(vectors),), dtype=np.bool_)
        for i, v in enumerate(vectors):
            if isinstance(v, list) and len(v) == dim:
                M[i, :] = np.array(v, dtype=np.float32)
                valid[i] = True
        matrices.append(M)
        valids.append(valid)

    if not matrices:
        raise ValueError("유효한 벡터 행렬이 없습니다")

    def _cosine_sim_matrix_row(mat: np.ndarray, idx: int) -> np.ndarray:
        q = mat[idx]
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return np.full((mat.shape[0],), -np.inf, dtype=np.float32)
        dot = mat @ q
        mat_norms = np.linalg.norm(mat, axis=1)
        denom = (mat_norms * q_norm)
        with np.errstate(divide='ignore', invalid='ignore'):
            sims = np.where(denom > 0, dot / denom, -np.inf)
        return sims

    if len(seeds) != 3:
        raise ValueError("seeds는 3개여야 합니다")
    seed_indices: List[int] = []
    for s in seeds:
        idx = _resolve_seed_to_index(s, titles)
        if idx is None:
            raise ValueError(f"seed를 찾을 수 없습니다: {s}")
        seed_indices.append(idx)
    seed_titles: List[str] = [titles[i] for i in seed_indices]

    per_seed_neighbors: List[List[int]] = []
    per_seed_neighbor_titles: List[List[str]] = []
    per_seed_top_labels: List[List[str]] = []
    per_seed_top_genres: List[List[str]] = []
    global_counts: Dict[str, int] = {}
    global_genre_counts: Dict[str, int] = {}

    for si in seed_indices:
        combined_neighbors: List[int] = []
        for mat, valid in zip(matrices, valids):
            if si >= len(valid) or not valid[si]:
                continue
            sims = _cosine_sim_matrix_row(mat, si)
            if si < sims.shape[0]:
                sims[si] = -np.inf
            nn_idx = np.argsort(-sims)
            nn_idx = [int(i) for i in nn_idx if valid[int(i)]]
            nn_idx = nn_idx[:max(0, k_neighbors)]
            combined_neighbors.extend(nn_idx)
        per_seed_neighbors.append(combined_neighbors)
        per_seed_neighbor_titles.append([titles[ni] for ni in combined_neighbors])

        counts: Dict[str, int] = {}
        genre_counts: Dict[str, int] = {}
        for ni in combined_neighbors:
            row = data_rows[ni]
            for li in label_indices:
                if li >= len(row):
                    continue
                cell = row[li]
                if not isinstance(cell, str) or not cell.strip():
                    continue
                parts = re.split(r"\s*[|,]\s*", cell.strip())
                for p in parts:
                    if not p:
                        continue
                    counts[p] = counts.get(p, 0) + 1
            if genre_idx_opt is not None and genre_idx_opt < len(row):
                gcell = row[genre_idx_opt]
                if isinstance(gcell, str) and gcell.strip():
                    gparts = re.split(r"\s*[|,]\s*", gcell.strip())
                    for gp in gparts:
                        if not gp:
                            continue
                        genre_counts[gp] = genre_counts.get(gp, 0) + 1

        top_items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:max(0, per_seed_top)]
        top_labels = [k for k, _ in top_items]
        per_seed_top_labels.append(top_labels)
        for k in top_labels:
            global_counts[k] = global_counts.get(k, 0) + 1

        top_g_items = sorted(genre_counts.items(), key=lambda x: (-x[1], x[0]))[:max(0, per_seed_top)]
        top_genres = [k for k, _ in top_g_items]
        per_seed_top_genres.append(top_genres)
        for k in top_genres:
            global_genre_counts[k] = global_genre_counts.get(k, 0) + 1

    final_top_labels = [k for k, _ in sorted(global_counts.items(), key=lambda x: (-x[1], x[0]))[:max(0, final_top)]]
    final_top_genres = [k for k, _ in sorted(global_genre_counts.items(), key=lambda x: (-x[1], x[0]))[:max(0, final_top)]]

    return {
        "seed_titles": seed_titles,
        "per_seed_top_labels": per_seed_top_labels,
        "per_seed_top_genres": per_seed_top_genres,
        "final_top_labels": final_top_labels,
        "final_top_genres": final_top_genres,
        "neighbors_indices": per_seed_neighbors,
        "per_seed_neighbor_titles": per_seed_neighbor_titles,
    }


def recommend_from_csv_with_indices(
    csv_path: str,
    a: int,
    b: int,
    c: int,
    k_neighbors: int = 3,
    per_seed_top: int = 3,
    final_top: int = 3,
    vector_cols: Optional[List[str]] = None,
) -> Dict[str, object]:
    """Convenience wrapper: pass three numbers, get recommendation results."""
    seeds: List[object] = [a, b, c]
    return recommend_by_knn_multi_vectors(
        csv_path=csv_path,
        seeds=seeds,
        k_neighbors=k_neighbors,
        per_seed_top=per_seed_top,
        final_top=final_top,
        vector_cols=vector_cols,
        label_col_candidates=None,
        title_col_candidates=None,
    )


def recommend_with_config_seeds(
    seeds: List[int],
    k_neighbors: int = 3,
    per_seed_top: int = 3,
    final_top: int = 3,
    vector_cols: Optional[List[str]] = None,
) -> Dict[str, object]:
    """Convenience wrapper using the fixed CSV path from config (CSV_SONGS_PATH)."""
    if not isinstance(seeds, list) or len(seeds) != 3:
        raise ValueError("seeds must be a list of 3 integers")
    return recommend_by_knn_multi_vectors(
        csv_path=CSV_SONGS_PATH,
        seeds=seeds,
        k_neighbors=k_neighbors,
        per_seed_top=per_seed_top,
        final_top=final_top,
        vector_cols=vector_cols,
        label_col_candidates=None,
        title_col_candidates=None,
    )
