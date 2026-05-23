"""Evaluation primitives."""

from t2i_core.evaluation.config import EvalModelConfig, EvalPreset, EvaluationThresholds
from t2i_core.evaluation.embedding import EmbeddingEvaluator

__all__ = [
    "EmbeddingEvaluator",
    "EvalModelConfig",
    "EvalPreset",
    "EvaluationThresholds",
]
