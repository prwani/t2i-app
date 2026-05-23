"""Evaluation model and threshold configuration."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class EvalPreset(StrEnum):
    """Named evaluation model presets."""

    COST_OPTIMIZED = "cost_optimized"
    UNIFIED_PREMIUM = "unified_premium"
    UNIFIED_BALANCED = "unified_balanced"
    BUDGET = "budget"
    CUSTOM = "custom"


class EvalModelConfig(BaseModel):
    """Deployment choices for evaluation layers."""

    preset: EvalPreset = EvalPreset.COST_OPTIMIZED
    decomposer_deployment: str = "o4-mini"
    rubric_deployment: str = "o4-mini"
    judge_deployment: str = "gpt-5.4"
    decomposer_is_o_series: bool = True
    rubric_is_o_series: bool = True
    judge_is_o_series: bool = False

    @classmethod
    def from_preset(cls, preset: EvalPreset) -> "EvalModelConfig":
        presets = {
            EvalPreset.COST_OPTIMIZED: dict(
                decomposer_deployment="o4-mini",
                rubric_deployment="o4-mini",
                judge_deployment="gpt-5.4",
                decomposer_is_o_series=True,
                rubric_is_o_series=True,
                judge_is_o_series=False,
            ),
            EvalPreset.UNIFIED_PREMIUM: dict(
                decomposer_deployment="gpt-5.5",
                rubric_deployment="gpt-5.5",
                judge_deployment="gpt-5.5",
                decomposer_is_o_series=False,
                rubric_is_o_series=False,
                judge_is_o_series=False,
            ),
            EvalPreset.UNIFIED_BALANCED: dict(
                decomposer_deployment="gpt-5.4",
                rubric_deployment="gpt-5.4",
                judge_deployment="gpt-5.4",
                decomposer_is_o_series=False,
                rubric_is_o_series=False,
                judge_is_o_series=False,
            ),
            EvalPreset.BUDGET: dict(
                decomposer_deployment="o4-mini",
                rubric_deployment="gpt-5-mini",
                judge_deployment="gpt-5.4-mini",
                decomposer_is_o_series=True,
                rubric_is_o_series=False,
                judge_is_o_series=False,
            ),
        }
        return cls(preset=preset, **presets[preset])


class EvaluationThresholds(BaseModel):
    """Configurable quality-gate thresholds."""

    embedding_min: float = Field(default=0.50, ge=-1.0, le=1.0)
    rubric_min: float = Field(default=0.70, ge=0.0, le=1.0)
    judge_min_average: float = Field(default=3.50, ge=1.0, le=5.0)
    composite_accept: float = Field(default=0.70, ge=0.0, le=1.0)
    composite_regenerate: float = Field(default=0.55, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_composite_order(self) -> "EvaluationThresholds":
        if self.composite_regenerate > self.composite_accept:
            raise ValueError("composite_regenerate must be <= composite_accept")
        return self
