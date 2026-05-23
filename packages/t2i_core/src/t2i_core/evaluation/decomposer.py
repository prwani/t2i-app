"""Prompt decomposition for image evaluation."""

from openai import AsyncOpenAI

from t2i_core.clients import get_openai_client
from t2i_core.evaluation.config import EvalModelConfig
from t2i_core.evaluation.openai_json import create_json_chat_completion
from t2i_core.settings import Settings
from t2i_core.types import Attribute


DECOMPOSER_INSTRUCTIONS = """Decompose an image generation prompt into atomic visual attributes.
Each attribute must be independently verifiable in a generated image.
Respond in JSON with this shape:
{"attributes":[{"category":"object|color|action|setting|lighting|style|text|count","description":"...","question":"Is ... visible?"}]}"""


class PromptDecomposer:
    """Break prompts into independently verifiable visual attributes."""

    def __init__(
        self,
        settings: Settings,
        model_config: EvalModelConfig | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.settings = settings
        self.model_config = model_config or settings.eval_model_config
        self.client = client or get_openai_client(settings)
        self._cache: dict[str, list[Attribute]] = {}

    async def decompose(self, prompt: str) -> list[Attribute]:
        """Return cached or newly decomposed prompt attributes."""

        cleaned = prompt.strip()
        if not cleaned:
            raise ValueError("prompt must not be empty")
        if cleaned in self._cache:
            return self._cache[cleaned]

        payload, _ = await create_json_chat_completion(
            self.client,
            model=self.model_config.decomposer_deployment,
            is_o_series=self.model_config.decomposer_is_o_series,
            instructions=DECOMPOSER_INSTRUCTIONS,
            user_content=f"Prompt: {cleaned}\nReturn JSON only.",
            max_tokens=4000,
        )
        raw_attributes = payload.get("attributes")
        if not isinstance(raw_attributes, list):
            raise ValueError("Prompt decomposition response did not include attributes")
        attributes = [_parse_attribute(item) for item in raw_attributes]
        self._cache[cleaned] = attributes
        return attributes


def _parse_attribute(item: object) -> Attribute:
    if not isinstance(item, dict):
        raise ValueError("Each decomposed attribute must be a JSON object")
    category = item.get("category")
    description = item.get("description")
    question = item.get("question")
    if not all(isinstance(value, str) and value.strip() for value in (category, description, question)):
        raise ValueError("Each decomposed attribute needs category, description, and question")
    return Attribute(category=category, description=description, question=question)
