import pytest
from pydantic import ValidationError

from t2i_core.evaluation.config import EvalPreset, EvaluationThresholds
from t2i_core.types import EmbeddingScore, GenerationResult


def test_generation_result_keeps_image_as_bytes(png_bytes: bytes) -> None:
    result = GenerationResult(
        image=png_bytes,
        prompt="red square",
        model="mai-image-2",
        size="1024x1024",
        quality="high",
    )

    assert isinstance(result.image, bytes)


def test_embedding_score_rejects_empty_vectors() -> None:
    with pytest.raises(ValidationError, match="must not be empty"):
        EmbeddingScore(
            text_vector=[],
            image_vector=[1.0],
            cosine_similarity=0.5,
            model_version="2023-04-15",
            vectorized_text="cat",
        )


def test_thresholds_validate_order() -> None:
    with pytest.raises(ValidationError, match="composite_regenerate"):
        EvaluationThresholds(composite_accept=0.4, composite_regenerate=0.5)


def test_eval_preset_builds_budget_config() -> None:
    config = EvalPreset.BUDGET

    assert config.value == "budget"
