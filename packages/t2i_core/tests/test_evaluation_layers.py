import json
from types import SimpleNamespace

import pytest

from t2i_core.evaluation.config import EvalModelConfig
from t2i_core.evaluation.decomposer import PromptDecomposer
from t2i_core.evaluation.judge import LLMJudgeEvaluator
from t2i_core.evaluation.openai_json import parse_json_object
from t2i_core.evaluation.pipeline import EvaluationPipeline, compute_composite_score
from t2i_core.evaluation.rubric import RubricEvaluator
from t2i_core.types import Attribute, CriterionScore, EmbeddingScore, LLMJudgeScore, RubricScore


class FakeChatCompletions:
    def __init__(self, payload):
        self.payload = payload
        self.kwargs = None
        self.calls = 0

    async def create(self, **kwargs):
        self.kwargs = kwargs
        self.calls += 1
        return SimpleNamespace(
            choices=[
                SimpleNamespace(message=SimpleNamespace(content=json.dumps(self.payload)))
            ]
        )


class FakeClient:
    def __init__(self, payload):
        self.chat = SimpleNamespace(completions=FakeChatCompletions(payload))


def test_parse_json_object_accepts_markdown_fence() -> None:
    assert parse_json_object('```json\n{"ok": true}\n```') == {"ok": True}


def test_parse_json_object_extracts_wrapped_object() -> None:
    assert parse_json_object('Here is the JSON: {"results": []}') == {"results": []}


@pytest.mark.asyncio
async def test_prompt_decomposer_uses_o_series_json_request_and_cache(settings) -> None:
    client = FakeClient(
        {
            "attributes": [
                {"category": "object", "description": "red square", "question": "Is there a red square?"}
            ]
        }
    )
    decomposer = PromptDecomposer(settings, client=client)  # type: ignore[arg-type]

    first = await decomposer.decompose("red square")
    second = await decomposer.decompose("red square")

    assert first == second
    assert client.chat.completions.calls == 1
    assert client.chat.completions.kwargs["messages"][0]["role"] == "developer"
    assert client.chat.completions.kwargs["max_completion_tokens"] == 4000
    assert client.chat.completions.kwargs["reasoning_effort"] == "low"


@pytest.mark.asyncio
async def test_rubric_evaluator_scores_attributes(settings, png_bytes: bytes) -> None:
    client = FakeClient({"results": [{"answer": "partial", "confidence": 0.8, "reasoning": "mostly visible"}]})
    evaluator = RubricEvaluator(settings, client=client)  # type: ignore[arg-type]
    attributes = [Attribute(category="object", description="red square", question="Is it a red square?")]

    score = await evaluator.evaluate(png_bytes, "red square", attributes=attributes)

    assert score.total_attributes == 1
    assert score.partial_attributes == 1
    assert score.rubric_score == 0.5


@pytest.mark.asyncio
async def test_judge_evaluator_parses_average(settings, png_bytes: bytes) -> None:
    client = FakeClient(
        {
            "visual_quality": {"score": 5, "justification": "clean"},
            "spatial_coherence": {"score": 4, "justification": "coherent"},
            "style_fidelity": {"score": 3, "justification": "ok"},
            "aesthetic_appeal": {"score": 4, "justification": "good"},
            "overall_impression": "solid image",
        }
    )
    evaluator = LLMJudgeEvaluator(settings, client=client)  # type: ignore[arg-type]

    score = await evaluator.evaluate(png_bytes, "red square")

    assert score.average_score == 4.0
    assert client.chat.completions.kwargs["messages"][0]["role"] == "system"
    assert client.chat.completions.kwargs["max_completion_tokens"] == 2000


def test_composite_score_normalizes_active_layers() -> None:
    composite = compute_composite_score(
        {"embedding_score": 0.2, "rubric_score": 0.45, "llm_judge_score": 0.35},
        embedding=EmbeddingScore(
            text_vector=[1.0],
            image_vector=[1.0],
            cosine_similarity=0.5,
            model_version="test",
            vectorized_text="red square",
        ),
        rubric=RubricScore(
            attributes=[],
            total_attributes=0,
            matched_attributes=0,
            partial_attributes=0,
            rubric_score=1.0,
        ),
        judge=LLMJudgeScore(
            visual_quality=CriterionScore(score=5, justification=""),
            spatial_coherence=CriterionScore(score=5, justification=""),
            style_fidelity=CriterionScore(score=5, justification=""),
            aesthetic_appeal=CriterionScore(score=5, justification=""),
            overall_impression="",
            average_score=5.0,
        ),
    )

    assert composite == pytest.approx(0.9)


@pytest.mark.asyncio
async def test_pipeline_selective_layer_skips_other_evaluators(settings, png_bytes: bytes) -> None:
    class FakeEmbedding:
        async def evaluate(self, image: bytes, prompt: str):
            return EmbeddingScore(
                text_vector=[1.0],
                image_vector=[1.0],
                cosine_similarity=0.8,
                model_version="test",
                vectorized_text=prompt,
            )

    class FailingEvaluator:
        async def evaluate(self, *args, **kwargs):
            raise AssertionError("should not run")

    pipeline = EvaluationPipeline(
        settings,
        model_config=EvalModelConfig(),
        embedding=FakeEmbedding(),  # type: ignore[arg-type]
        rubric=FailingEvaluator(),  # type: ignore[arg-type]
        judge=FailingEvaluator(),  # type: ignore[arg-type]
    )

    report = await pipeline.evaluate(png_bytes, "red square", layers=["embedding"])

    assert report.layers_run == ["embedding"]
    assert report.composite_score == pytest.approx(0.8)
