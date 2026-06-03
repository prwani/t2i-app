"""Request and response models for the backend API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ImageModel = Literal[
    "gpt-image-2",
    "MAI-Image-2",
    "MAI-Image-2e",
    "MAI-Image-2.5-Flash",
    "MAI-Image-2.5",
]
LayerName = Literal["embedding", "rubric", "judge"]
JobStatus = Literal["queued", "running", "succeeded", "failed"]


class ScenarioResponse(BaseModel):
    id: str
    label: str
    default_model: str
    forced_model: str | None
    model_options: list[str] = Field(default_factory=list)
    example_prompts: list[str]
    example_extras: list[dict[str, Any]] = Field(default_factory=list)
    recommended_eval_layers: list[LayerName]
    evaluation_recommended: bool
    compare_recommended: bool


class ImprovePromptRequest(BaseModel):
    scenario: str
    prompt: str = Field(min_length=1)


class ImprovePromptResponse(BaseModel):
    prompt: str


class AssetInput(BaseModel):
    id: str | None = None
    data: str | None = None
    name: str | None = None
    prompt: str | None = None
    model: str | None = None


class GenerationRequest(BaseModel):
    scenario: str = "text-to-image"
    prompt: str = Field(min_length=1)
    model: ImageModel | None = None
    size: str = "1024x1024"
    quality: Literal["low", "medium", "high"] = "high"
    n: int = Field(default=1, ge=1, le=4)
    evaluate: bool = False
    layers: list[LayerName] | None = None
    source_images: list[AssetInput] = Field(default_factory=list)
    mask: AssetInput | None = None
    formats: list[str] = Field(default_factory=list)
    brand_colors: list[str] = Field(default_factory=list)
    font_style: str | None = None
    tone: str | None = None
    logo_description: str | None = None
    text: str | None = None
    environments: list[str] = Field(default_factory=list)
    refinements: list[str] = Field(default_factory=list)


class AssetResponse(BaseModel):
    id: str
    name: str
    url: str
    prompt: str
    revised_prompt: str | None = None
    model: str
    size: str
    quality: str
    caption: str | None = None
    evaluation: dict[str, Any] | None = None


class GenerationJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    assets: list[AssetResponse] = Field(default_factory=list)
    error: str | None = None


class EvaluationRequest(BaseModel):
    prompt: str = Field(min_length=1)
    layers: list[LayerName] = Field(default_factory=lambda: ["embedding", "rubric", "judge"])
    assets: list[AssetInput] = Field(min_length=1)


class EvaluationReportResponse(BaseModel):
    asset_id: str | None = None
    name: str | None = None
    report: dict[str, Any]


class EvaluationResponse(BaseModel):
    job_id: str
    status: JobStatus
    reports: list[EvaluationReportResponse] = Field(default_factory=list)
    error: str | None = None


class ComparisonResponse(EvaluationResponse):
    ranked: list[EvaluationReportResponse] = Field(default_factory=list)
