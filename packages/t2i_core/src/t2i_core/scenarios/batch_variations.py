"""Batch variation generation and ranking scenario."""

from pydantic import BaseModel

from t2i_core.evaluation.pipeline import EvaluationLayer, EvaluationPipeline
from t2i_core.providers.base import ImageProvider
from t2i_core.types import EvaluationReport, GenerationResult


class RankedVariation(BaseModel):
    """Generated variation with optional evaluation report."""

    rank: int
    generation: GenerationResult
    evaluation: EvaluationReport | None = None


async def generate_ranked_variations(
    provider: ImageProvider,
    prompt: str,
    *,
    n: int = 4,
    size: str = "1024x1024",
    quality: str = "high",
    pipeline: EvaluationPipeline | None = None,
    layers: list[EvaluationLayer] | None = None,
) -> list[RankedVariation]:
    """Generate N variations and optionally rank by evaluation composite score."""

    if not 1 <= n <= 10:
        raise ValueError("n must be between 1 and 10")
    generations = await provider.generate(prompt, size=size, quality=quality, n=n)
    reports: list[EvaluationReport | None] = []
    if pipeline is not None:
        for generation in generations:
            reports.append(
                await pipeline.evaluate(
                    generation.image,
                    prompt,
                    layers=layers,
                    model_used=generation.model,
                )
            )
    else:
        reports = [None] * len(generations)

    paired = list(zip(generations, reports, strict=True))
    paired.sort(key=lambda item: item[1].composite_score if item[1] is not None else 0.0, reverse=True)
    return [
        RankedVariation(rank=index + 1, generation=generation, evaluation=report)
        for index, (generation, report) in enumerate(paired)
    ]
