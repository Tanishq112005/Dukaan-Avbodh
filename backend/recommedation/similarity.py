import numpy as np
from typing import List


def calculate_cosine_similarity(query_vec, candidate_matrix) -> List[float]:
    """
    Computes mathematical Cosine Similarity using sentence_transformers.util.cos_sim
    with a lightweight NumPy fallback. Keeps the codebase minimal and fast.
    """
    try:
        from sentence_transformers.util import cos_sim
        scores = cos_sim(query_vec, candidate_matrix)
        if hasattr(scores, "cpu"):
            scores = scores.cpu().numpy()
        arr = np.array(scores)
        return [max(0.0, float(s)) for s in (arr[0] if arr.ndim > 1 else arr)]
    except Exception:
        a = np.array(query_vec, dtype=np.float32)
        b = np.array(candidate_matrix, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b, axis=1) if b.ndim > 1 else np.linalg.norm(b)
        dot = np.dot(b, a)
        denom = np.where(norm_a * norm_b == 0.0, 1e-9, norm_a * norm_b)
        return [max(0.0, float(s)) for s in np.clip(dot / denom, 0.0, 1.0)]
