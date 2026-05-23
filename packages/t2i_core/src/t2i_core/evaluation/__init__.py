"""Evaluation primitives."""

from t2i_core.evaluation.config import EvalModelConfig, EvalPreset, EvaluationThresholds
from t2i_core.evaluation.decomposer import PromptDecomposer
from t2i_core.evaluation.embedding import EmbeddingEvaluator
from t2i_core.evaluation.judge import LLMJudgeEvaluator
from t2i_core.evaluation.pipeline import EvaluationPipeline
from t2i_core.evaluation.rubric import RubricEvaluator

__all__ = [
    "EmbeddingEvaluator",
    "EvaluationPipeline",
    "EvalModelConfig",
    "EvalPreset",
    "EvaluationThresholds",
    "LLMJudgeEvaluator",
    "PromptDecomposer",
    "RubricEvaluator",
]
