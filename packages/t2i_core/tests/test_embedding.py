import pytest
import respx
from httpx import Response

from t2i_core.evaluation.embedding import (
    VISION_API_VERSION,
    VISION_MODEL_VERSION,
    EmbeddingEvaluator,
    cosine_similarity,
)


def test_cosine_similarity_uses_raw_score() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


@pytest.mark.asyncio
@respx.mock
async def test_embedding_evaluator_calls_vision_with_bearer_and_raw_bytes(
    settings,
    png_bytes: bytes,
) -> None:
    text_url = (
        f"{settings.vision_endpoint}/computervision/retrieval:vectorizeText"
        f"?api-version={VISION_API_VERSION}&model-version={VISION_MODEL_VERSION}"
    )
    image_url = (
        f"{settings.vision_endpoint}/computervision/retrieval:vectorizeImage"
        f"?api-version={VISION_API_VERSION}&model-version={VISION_MODEL_VERSION}"
    )
    text_route = respx.post(text_url).mock(return_value=Response(200, json={"vector": [1.0, 0.0]}))
    image_route = respx.post(image_url).mock(return_value=Response(200, json={"vector": [1.0, 0.0]}))
    evaluator = EmbeddingEvaluator(settings=settings, token_provider=lambda: "fake-token")

    score = await evaluator.evaluate(png_bytes, "red square")

    assert score.cosine_similarity == 1.0
    assert text_route.called
    assert image_route.called
    text_request = text_route.calls.last.request
    image_request = image_route.calls.last.request
    assert text_request.headers["Authorization"] == "Bearer fake-token"
    assert image_request.headers["Authorization"] == "Bearer fake-token"
    assert text_request.headers["Content-Type"] == "application/json"
    assert image_request.headers["Content-Type"] == "application/octet-stream"
    assert image_request.content == png_bytes


def test_embedding_prompt_is_trimmed_to_vision_limit(settings) -> None:
    evaluator = EmbeddingEvaluator(settings=settings, token_provider=lambda: "fake-token")
    long_prompt = " ".join(f"word{i}" for i in range(90))

    prepared = evaluator._prepare_embedding_prompt(long_prompt)

    assert len(prepared.split()) == 70
