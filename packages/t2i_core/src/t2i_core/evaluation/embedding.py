"""Layer 1 embedding-based image evaluation."""

import math
from collections.abc import Callable

import httpx

from t2i_core.clients import get_http_client, get_vision_token_provider
from t2i_core.settings import Settings
from t2i_core.types import EmbeddingScore
from t2i_core.utils import trim_to_word_limit, validate_image_for_vision


VISION_API_VERSION = "2024-02-01"
VISION_MODEL_VERSION = "2023-04-15"
VISION_TEXT_WORD_LIMIT = 70


class EmbeddingEvaluator:
    """Standalone Layer 1 evaluator using Azure AI Vision multimodal embeddings."""

    def __init__(
        self,
        settings: Settings,
        http_client: httpx.AsyncClient | None = None,
        token_provider: Callable[[], str] | None = None,
    ) -> None:
        self.settings = settings
        self.http_client = http_client or get_http_client()
        self.token_provider = token_provider or get_vision_token_provider(settings)

    async def evaluate(self, image: bytes, prompt: str) -> EmbeddingScore:
        """Run embedding similarity evaluation independently."""

        validate_image_for_vision(image)
        vectorized_text = self._prepare_embedding_prompt(prompt)
        text_vector = await self._vectorize_text(vectorized_text)
        image_vector = await self._vectorize_image(image)
        return EmbeddingScore(
            text_vector=text_vector,
            image_vector=image_vector,
            cosine_similarity=cosine_similarity(text_vector, image_vector),
            model_version=VISION_MODEL_VERSION,
            vectorized_text=vectorized_text,
        )

    def _prepare_embedding_prompt(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        return trim_to_word_limit(prompt, VISION_TEXT_WORD_LIMIT)

    async def _vectorize_text(self, text: str) -> list[float]:
        response = await self.http_client.post(
            self._vision_url("retrieval:vectorizeText"),
            headers=self._headers("application/json"),
            json={"text": text},
        )
        response.raise_for_status()
        return _extract_vector(response.json())

    async def _vectorize_image(self, image: bytes) -> list[float]:
        response = await self.http_client.post(
            self._vision_url("retrieval:vectorizeImage"),
            headers=self._headers("application/octet-stream"),
            content=image,
        )
        response.raise_for_status()
        return _extract_vector(response.json())

    def _headers(self, content_type: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token_provider()}",
            "Content-Type": content_type,
        }

    def _vision_url(self, operation: str) -> str:
        return (
            f"{self.settings.vision_endpoint}/computervision/{operation}"
            f"?api-version={VISION_API_VERSION}&model-version={VISION_MODEL_VERSION}"
        )


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """Compute raw cosine similarity; Azure Vision scores are not rescaled."""

    if len(vector_a) != len(vector_b):
        raise ValueError("vectors must have the same length")
    dot = sum(a * b for a, b in zip(vector_a, vector_b, strict=True))
    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))
    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError("vectors must have non-zero magnitude")
    return dot / (magnitude_a * magnitude_b)


def _extract_vector(payload: object) -> list[float]:
    if not isinstance(payload, dict):
        raise ValueError("Azure AI Vision response must be a JSON object")
    vector = payload.get("vector")
    if not isinstance(vector, list) or not all(isinstance(value, int | float) for value in vector):
        raise ValueError("Azure AI Vision response did not include a numeric vector")
    return [float(value) for value in vector]
