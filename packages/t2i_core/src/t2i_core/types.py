"""Shared Pydantic models for generation and evaluation."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UsageCost(BaseModel):
    """Best-effort usage and cost metadata."""

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)


class GenerationResult(BaseModel):
    """Image generation result with bytes as the internal representation."""

    image: bytes
    prompt: str
    revised_prompt: str | None = None
    model: str
    size: str
    quality: str
    usage: UsageCost = Field(default_factory=UsageCost)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EditResult(GenerationResult):
    """Image edit result."""

    source_image_count: int = Field(ge=1)
    mask_used: bool = False


class VideoResult(BaseModel):
    """Video generation job or completed output."""

    job_id: str
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    video: bytes | None = None
    model: str
    prompt: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    seconds: int = Field(gt=0)
    usage: UsageCost = Field(default_factory=UsageCost)


class EmbeddingScore(BaseModel):
    """Layer 1 semantic-alignment score from multimodal embeddings."""

    text_vector: list[float]
    image_vector: list[float]
    cosine_similarity: float = Field(ge=-1.0, le=1.0)
    model_version: str
    vectorized_text: str

    @field_validator("text_vector", "image_vector")
    @classmethod
    def vectors_must_not_be_empty(cls, value: list[float]) -> list[float]:
        if not value:
            raise ValueError("embedding vectors must not be empty")
        return value


class Attribute(BaseModel):
    """Atomic visual attribute extracted from a prompt."""

    category: str
    description: str
    question: str


class AttributeResult(BaseModel):
    """Rubric result for one prompt attribute."""

    category: str
    description: str
    question: str
    answer: Literal["yes", "no", "partial"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class RubricScore(BaseModel):
    """Layer 2 prompt-adherence score."""

    attributes: list[AttributeResult]
    total_attributes: int = Field(ge=0)
    matched_attributes: int = Field(ge=0)
    partial_attributes: int = Field(ge=0)
    rubric_score: float = Field(ge=0.0, le=1.0)


class CriterionScore(BaseModel):
    """Layer 3 judge score for one quality criterion."""

    score: int = Field(ge=1, le=5)
    justification: str


class LLMJudgeScore(BaseModel):
    """Layer 3 quality/aesthetic evaluation."""

    visual_quality: CriterionScore
    spatial_coherence: CriterionScore
    style_fidelity: CriterionScore
    aesthetic_appeal: CriterionScore
    text_legibility: CriterionScore | None = None
    overall_impression: str
    average_score: float = Field(ge=1.0, le=5.0)


class EvaluationReport(BaseModel):
    """Composite evaluation output."""

    prompt: str
    model_used: str | None = None
    image_path: str | None = None
    layers_run: list[str]
    embedding: EmbeddingScore | None = None
    rubric: RubricScore | None = None
    llm_judge: LLMJudgeScore | None = None
    weights: dict[str, float]
    composite_score: float = Field(ge=0.0, le=1.0)
    generation_time_ms: int | None = Field(default=None, ge=0)
    evaluation_time_ms: int = Field(ge=0)
    total_cost_estimate: float = Field(ge=0.0)
    threshold_decision: Literal["accept", "review", "regenerate"]
    threshold_reasons: list[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
