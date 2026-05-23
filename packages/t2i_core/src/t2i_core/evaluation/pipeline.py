"""Full image evaluation pipeline."""

import time
from typing import Literal

from t2i_core.evaluation.config import EvalModelConfig
from t2i_core.evaluation.decomposer import PromptDecomposer
from t2i_core.evaluation.embedding import EmbeddingEvaluator
from t2i_core.evaluation.judge import LLMJudgeEvaluator
from t2i_core.evaluation.rubric import RubricEvaluator
from t2i_core.settings import Settings
from t2i_core.types import EmbeddingScore, EvaluationReport, LLMJudgeScore, RubricScore


EvaluationLayer = Literal["embedding", "rubric", "judge"]
DEFAULT_LAYERS: tuple[EvaluationLayer, ...] = ("embedding", "rubric", "judge")


class EvaluationPipeline:
    """Orchestrate standalone evaluators with selective layer execution."""

    def __init__(
        self,
        settings: Settings,
        model_config: EvalModelConfig | None = None,
        embedding: EmbeddingEvaluator | None = None,
        rubric: RubricEvaluator | None = None,
        judge: LLMJudgeEvaluator | None = None,
    ) -> None:
        self.settings = settings
        self.model_config = model_config or settings.eval_model_config
        self.weights = settings.eval_weights
        self.embedding = embedding or EmbeddingEvaluator(settings)
        decomposer = PromptDecomposer(settings, self.model_config)
        self.rubric = rubric or RubricEvaluator(settings, self.model_config, decomposer=decomposer)
        self.judge = judge or LLMJudgeEvaluator(settings, self.model_config)

    async def evaluate(
        self,
        image: bytes,
        prompt: str,
        layers: list[EvaluationLayer] | None = None,
        model_used: str | None = None,
        image_path: str | None = None,
        generation_time_ms: int | None = None,
    ) -> EvaluationReport:
        """Run the selected layers and return a normalized composite report."""

        start = time.perf_counter()
        selected = list(layers or DEFAULT_LAYERS)
        _validate_layers(selected)

        embedding_score = await self.embedding.evaluate(image, prompt) if "embedding" in selected else None
        rubric_score = await self.rubric.evaluate(image, prompt) if "rubric" in selected else None
        judge_score = await self.judge.evaluate(image, prompt) if "judge" in selected else None
        composite = compute_composite_score(
            self.weights,
            embedding=embedding_score,
            rubric=rubric_score,
            judge=judge_score,
        )
        decision, reasons = threshold_decision(self.settings, embedding_score, rubric_score, judge_score, composite)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return EvaluationReport(
            prompt=prompt,
            model_used=model_used,
            image_path=image_path,
            layers_run=selected,
            embedding=embedding_score,
            rubric=rubric_score,
            llm_judge=judge_score,
            weights=self.weights,
            composite_score=composite,
            generation_time_ms=generation_time_ms,
            evaluation_time_ms=elapsed_ms,
            total_cost_estimate=0.0,
            threshold_decision=decision,
            threshold_reasons=reasons,
        )


def compute_composite_score(
    weights: dict[str, float],
    *,
    embedding: EmbeddingScore | None = None,
    rubric: RubricScore | None = None,
    judge: LLMJudgeScore | None = None,
) -> float:
    """Compute a 0-1 composite score using only layers that ran."""

    weighted_scores: list[tuple[float, float]] = []
    if embedding is not None:
        weighted_scores.append((weights.get("embedding_score", 0.0), max(0.0, embedding.cosine_similarity)))
    if rubric is not None:
        weighted_scores.append((weights.get("rubric_score", 0.0), rubric.rubric_score))
    if judge is not None:
        weighted_scores.append((weights.get("llm_judge_score", 0.0), (judge.average_score - 1.0) / 4.0))
    active_weight = sum(weight for weight, _ in weighted_scores if weight > 0)
    if active_weight == 0:
        raise ValueError("at least one selected evaluation layer must have a positive weight")
    return sum(weight * score for weight, score in weighted_scores if weight > 0) / active_weight


def threshold_decision(
    settings: Settings,
    embedding: EmbeddingScore | None,
    rubric: RubricScore | None,
    judge: LLMJudgeScore | None,
    composite: float,
) -> tuple[Literal["accept", "review", "regenerate"], list[str]]:
    thresholds = settings.eval_thresholds
    reasons: list[str] = []
    if embedding is not None and embedding.cosine_similarity < thresholds.embedding_min:
        reasons.append("embedding score below minimum")
    if rubric is not None and rubric.rubric_score < thresholds.rubric_min:
        reasons.append("rubric score below minimum")
    if judge is not None and judge.average_score < thresholds.judge_min_average:
        reasons.append("judge average below minimum")
    if composite < thresholds.composite_regenerate:
        reasons.append("composite score below regenerate threshold")
    if reasons:
        return "regenerate", reasons
    if composite >= thresholds.composite_accept:
        return "accept", ["all selected layers met thresholds"]
    return "review", ["composite score below accept threshold"]


def _validate_layers(layers: list[str]) -> None:
    valid = set(DEFAULT_LAYERS)
    invalid = sorted(set(layers) - valid)
    if invalid:
        raise ValueError(f"Unsupported evaluation layers: {', '.join(invalid)}")
    if not layers:
        raise ValueError("at least one evaluation layer is required")
