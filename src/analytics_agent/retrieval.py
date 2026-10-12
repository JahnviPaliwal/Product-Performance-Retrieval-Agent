"""Column retrieval module using Sentence-Transformers and FAISS for wide-dataset indexing and semantic selection.
"""

from typing import Any, Dict, List, Optional
import numpy as np


class ColumnRetriever:
    """Indexes column semantic summaries with Sentence-Transformers and FAISS."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize the embedding model and vector index state."""
        self.model_name = model_name
        self._model = None
        self._index = None
        self._columns: List[Dict[str, Any]] = []
        self._initialized = False

    def _load_model(self) -> None:
        """Lazy load sentence-transformers model to conserve memory until needed."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._initialized = True
            except Exception as e:
                self._initialized = False
                raise RuntimeError(f"Could not load SentenceTransformer '{self.model_name}': {e}") from e

    def build_index(self, columns: List[Dict[str, Any]]) -> None:
        """Embed column profiles and create in-memory FAISS index.

        Args:
            columns: List of column profile dictionaries.
        """
        if not columns:
            self._columns = []
            self._index = None
            return

        self._load_model()
        import faiss

        self._columns = columns
        texts = []
        for col in columns:
            name = col.get("name", "")
            dtype = col.get("dtype", "")
            summary = col.get("semantic_summary", "")
            samples = ", ".join(col.get("sample_values", []))
            text = f"Column: {name}. Type: {dtype}. Summary: {summary}. Sample values: {samples}."
            texts.append(text)

        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product on normalized vectors = cosine similarity
        index.add(embeddings)
        self._index = index

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Retrieve top-k most relevant columns for a user question or analytical prompt.

        Args:
            query: The user question or analytical objective string.
            top_k: Number of relevant columns to retrieve.

        Returns:
            List of matching column profile dictionaries.
        """
        if not self._index or not self._columns:
            return self._columns

        k = min(top_k, len(self._columns))
        if k <= 0:
            return []

        self._load_model()
        query_vec = self._model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        query_vec = np.ascontiguousarray(query_vec, dtype=np.float32)

        distances, indices = self._index.search(query_vec, k)
        matched_cols = []
        for idx in indices[0]:
            if 0 <= idx < len(self._columns):
                matched_cols.append(self._columns[idx])

        return matched_cols


def filter_profile_for_query(
    profile: Dict[str, Any],
    query: Optional[str] = None,
    top_k: int = 8,
    enable_retrieval: bool = True,
) -> Dict[str, Any]:
    """Prune wide dataset profile by retrieving top-k semantically relevant columns.

    Args:
        profile: The full dataset profile dict.
        query: Optional question or analytical intent.
        top_k: Maximum columns to keep if retrieval is enabled.
        enable_retrieval: Flag to toggle retrieval layer.

    Returns:
        Pruned or original dataset profile dict with retrieval metadata.
    """
    total_cols = profile.get("num_columns", len(profile.get("columns", [])))

    # If retrieval is disabled or dataset is not wide, return profile as-is
    if not enable_retrieval or not query or total_cols <= top_k:
        profile_copy = dict(profile)
        profile_copy["retrieval_applied"] = False
        return profile_copy

    try:
        retriever = ColumnRetriever()
        retriever.build_index(profile.get("columns", []))
        relevant_cols = retriever.retrieve(query, top_k=top_k)

        pruned_profile = dict(profile)
        pruned_profile["columns"] = relevant_cols
        pruned_profile["num_columns_retained"] = len(relevant_cols)
        pruned_profile["retrieval_applied"] = True
        pruned_profile["retrieval_query"] = query
        return pruned_profile

    except Exception:
        # Graceful fallback: return unpruned profile without failing
        fallback_profile = dict(profile)
        fallback_profile["retrieval_applied"] = False
        return fallback_profile


def retrieve_relevant_columns(
    df_profile: Dict[str, Any],
    query: str,
    top_k: int = 8,
    enable_retrieval: bool = True,
) -> List[str]:
    """Convenience helper returning just the names of the top-k retrieved columns."""
    filtered = filter_profile_for_query(df_profile, query=query, top_k=top_k, enable_retrieval=enable_retrieval)
    return [col["name"] for col in filtered.get("columns", [])]
