from typing import List, Optional
import httpx


class SemanticSimilarityScorer:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - depends on installed extras
            raise RuntimeError(
                "Semantic agreement requires sentence-transformers. "
                "Install the project dependencies again."
            ) from exc

        self._model = SentenceTransformer(model_name)
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def average_similarity(self, texts: List[str]) -> float:
        if len(texts) < 2:
            return 1.0

        embeddings = self._model.encode(texts, normalize_embeddings=True)
        similarities = []
        for index, left in enumerate(embeddings):
            for right in embeddings[index + 1 :]:
                similarities.append(float(left @ right))

        return sum(similarities) / len(similarities)


class OllamaSemanticSimilarityScorer:
    def __init__(self, base_url: str, model_name: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def average_similarity(self, texts: List[str]) -> float:
        if len(texts) < 2:
            return 1.0

        embeddings = [self._embed(text) for text in texts]
        similarities = []
        for index, left in enumerate(embeddings):
            for right in embeddings[index + 1 :]:
                similarities.append(_cosine_similarity(left, right))

        return sum(similarities) / len(similarities)

    def _embed(self, text: str) -> List[float]:
        payload = {
            "model": self._model_name,
            "input": text,
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{self._base_url}/api/embed", json=payload)
            response.raise_for_status()
            body = response.json()
        return body["embeddings"][0]


_scorer_cache = {}


def get_semantic_similarity_scorer(
    model_name: str,
) -> Optional[SemanticSimilarityScorer]:
    if model_name in _scorer_cache:
        return _scorer_cache[model_name]

    try:
        scorer = SemanticSimilarityScorer(model_name)
    except Exception:
        return None

    _scorer_cache[model_name] = scorer
    return scorer


def get_ollama_semantic_similarity_scorer(
    base_url: str,
    model_name: str,
) -> Optional[OllamaSemanticSimilarityScorer]:
    cache_key = f"{base_url}::{model_name}"
    if cache_key in _scorer_cache:
        return _scorer_cache[cache_key]

    try:
        scorer = OllamaSemanticSimilarityScorer(base_url, model_name)
        scorer.average_similarity(["hello", "hello there"])
    except Exception:
        return None

    _scorer_cache[cache_key] = scorer
    return scorer


def _cosine_similarity(left: List[float], right: List[float]) -> float:
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0

    dot = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot / (left_norm * right_norm)
