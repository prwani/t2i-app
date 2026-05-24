"""Layer 2 rubric-based prompt adherence evaluation."""

from typing import Any

from openai import AsyncOpenAI

from t2i_core.clients import get_openai_client
from t2i_core.evaluation.config import EvalModelConfig
from t2i_core.evaluation.decomposer import PromptDecomposer
from t2i_core.evaluation.openai_json import create_json_chat_completion
from t2i_core.settings import Settings
from t2i_core.types import Attribute, AttributeResult, RubricScore
from t2i_core.utils import encode_base64_image, validate_image_for_vision


RUBRIC_INSTRUCTIONS = """You are a precise image evaluator. Answer each question about the image.
Do not judge aesthetics; only verify whether requested prompt attributes are present.
Respond with only a valid JSON object. Do not wrap it in markdown or prose. Use this shape:
{"results":[{"answer":"yes|no|partial","confidence":0.0,"reasoning":"..."}]}"""


class RubricEvaluator:
    """Standalone Layer 2 evaluator for prompt adherence."""

    def __init__(
        self,
        settings: Settings,
        model_config: EvalModelConfig | None = None,
        client: AsyncOpenAI | None = None,
        decomposer: PromptDecomposer | None = None,
    ) -> None:
        self.settings = settings
        self.model_config = model_config or settings.eval_model_config
        self.client = client or get_openai_client(settings)
        self.decomposer = decomposer or PromptDecomposer(settings, self.model_config, self.client)

    async def evaluate(
        self,
        image: bytes,
        prompt: str,
        attributes: list[Attribute] | None = None,
    ) -> RubricScore:
        """Run rubric evaluation, decomposing the prompt if needed."""

        validate_image_for_vision(image)
        checked_attributes = attributes or await self.decomposer.decompose(prompt)
        if not checked_attributes:
            raise ValueError("at least one attribute is required for rubric evaluation")

        user_content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    f"Prompt: {prompt}\n"
                    "Questions to answer as JSON results in the same order:\n"
                    + "\n".join(
                        f"{index + 1}. [{attribute.category}] {attribute.question}"
                        for index, attribute in enumerate(checked_attributes)
                    )
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{encode_base64_image(image)}"},
            },
        ]
        payload, _ = await create_json_chat_completion(
            self.client,
            model=self.model_config.rubric_deployment,
            is_o_series=self.model_config.rubric_is_o_series,
            instructions=RUBRIC_INSTRUCTIONS,
            user_content=user_content,
            max_tokens=2500,
        )
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise ValueError("Rubric response did not include results")
        results = [
            _parse_attribute_result(attribute, raw)
            for attribute, raw in zip(checked_attributes, raw_results, strict=False)
        ]
        if len(results) != len(checked_attributes):
            raise ValueError("Rubric response result count did not match attributes")
        matched = sum(1 for result in results if result.answer == "yes")
        partial = sum(1 for result in results if result.answer == "partial")
        score = (matched + 0.5 * partial) / len(results)
        return RubricScore(
            attributes=results,
            total_attributes=len(results),
            matched_attributes=matched,
            partial_attributes=partial,
            rubric_score=score,
        )


def _parse_attribute_result(attribute: Attribute, raw: object) -> AttributeResult:
    if not isinstance(raw, dict):
        raise ValueError("Each rubric result must be a JSON object")
    answer = raw.get("answer")
    confidence = raw.get("confidence")
    reasoning = raw.get("reasoning")
    if answer not in {"yes", "no", "partial"}:
        raise ValueError("Rubric answer must be yes, no, or partial")
    if not isinstance(confidence, int | float):
        raise ValueError("Rubric confidence must be numeric")
    if not isinstance(reasoning, str):
        raise ValueError("Rubric reasoning must be text")
    return AttributeResult(
        category=attribute.category,
        description=attribute.description,
        question=attribute.question,
        answer=answer,
        confidence=float(confidence),
        reasoning=reasoning,
    )
