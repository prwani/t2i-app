"""Layer 3 LLM-as-judge image quality evaluation."""

from typing import Any

from openai import AsyncOpenAI

from t2i_core.clients import get_openai_client
from t2i_core.evaluation.config import EvalModelConfig
from t2i_core.evaluation.openai_json import create_json_chat_completion
from t2i_core.settings import Settings
from t2i_core.types import CriterionScore, LLMJudgeScore
from t2i_core.utils import encode_base64_image, validate_image_for_vision


JUDGE_INSTRUCTIONS = """You are an expert image quality judge.
Score visual quality, spatial coherence, style fidelity, aesthetic appeal, and text legibility only when relevant.
Every score must be an integer from 1 to 5 inclusive. Never use a 0-10 or percentage scale.
Do not score prompt adherence; that is handled by a separate rubric evaluator.
Respond in JSON with this shape:
{"visual_quality":{"score":1,"justification":"..."},"spatial_coherence":{"score":1,"justification":"..."},"style_fidelity":{"score":1,"justification":"..."},"aesthetic_appeal":{"score":1,"justification":"..."},"text_legibility":{"score":1,"justification":"..."},"overall_impression":"..."}"""


class LLMJudgeEvaluator:
    """Standalone Layer 3 evaluator for holistic image quality."""

    def __init__(
        self,
        settings: Settings,
        model_config: EvalModelConfig | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.settings = settings
        self.model_config = model_config or settings.eval_model_config
        self.client = client or get_openai_client(settings)

    async def evaluate(self, image: bytes, prompt: str) -> LLMJudgeScore:
        """Run LLM judge evaluation independently."""

        validate_image_for_vision(image)
        user_content: list[dict[str, Any]] = [
            {"type": "text", "text": f"Prompt for context only: {prompt}\nReturn JSON only."},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{encode_base64_image(image)}"},
            },
        ]
        payload, _ = await create_json_chat_completion(
            self.client,
            model=self.model_config.judge_deployment,
            is_o_series=self.model_config.judge_is_o_series,
            instructions=JUDGE_INSTRUCTIONS,
            user_content=user_content,
            max_tokens=2000,
        )
        text_legibility = payload.get("text_legibility")
        criteria = [
            _parse_criterion(payload, "visual_quality"),
            _parse_criterion(payload, "spatial_coherence"),
            _parse_criterion(payload, "style_fidelity"),
            _parse_criterion(payload, "aesthetic_appeal"),
        ]
        parsed_text_legibility = (
            _parse_criterion(payload, "text_legibility")
            if isinstance(text_legibility, dict)
            else None
        )
        if parsed_text_legibility is not None:
            criteria.append(parsed_text_legibility)
        overall = payload.get("overall_impression")
        if not isinstance(overall, str):
            raise ValueError("Judge response must include overall_impression")
        average = sum(criterion.score for criterion in criteria) / len(criteria)
        return LLMJudgeScore(
            visual_quality=criteria[0],
            spatial_coherence=criteria[1],
            style_fidelity=criteria[2],
            aesthetic_appeal=criteria[3],
            text_legibility=parsed_text_legibility,
            overall_impression=overall,
            average_score=average,
        )


def _parse_criterion(payload: dict[str, Any], key: str) -> CriterionScore:
    raw = payload.get(key)
    if not isinstance(raw, dict):
        raise ValueError(f"Judge response must include {key}")
    score = raw.get("score")
    justification = raw.get("justification")
    if not isinstance(score, int):
        raise ValueError(f"{key}.score must be an integer")
    if not isinstance(justification, str):
        raise ValueError(f"{key}.justification must be text")
    return CriterionScore(score=score, justification=justification)
