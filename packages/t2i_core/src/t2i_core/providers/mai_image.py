"""MAI image provider."""

from collections.abc import Callable
from typing import Any

from openai import AsyncOpenAI

from t2i_core.clients import get_openai_client
from t2i_core.settings import Settings
from t2i_core.types import GenerationResult
from t2i_core.utils import decode_base64_image


class MAIImageProvider:
    """Provider for MAI-Image deployments using the Azure OpenAI v1 image API."""

    def __init__(
        self,
        settings: Settings,
        client: AsyncOpenAI | None = None,
        deployment: str | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or get_openai_client(settings)
        self.deployment = deployment or settings.mai_image_deployment

    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1,
    ) -> list[GenerationResult]:
        """Generate image bytes from a text prompt."""

        response = await self.client.images.generate(
            model=self.deployment,
            prompt=prompt,
            n=n,
            size=size,
            quality=quality,
            output_format="png",
        )

        data = _extract_response_data(response)
        results: list[GenerationResult] = []
        for item in data:
            b64_json = _get_value(item, "b64_json")
            if not isinstance(b64_json, str) or not b64_json:
                raise ValueError("Image generation response did not include b64_json")
            revised_prompt = _get_value(item, "revised_prompt")
            results.append(
                GenerationResult(
                    image=decode_base64_image(b64_json),
                    prompt=prompt,
                    revised_prompt=revised_prompt if isinstance(revised_prompt, str) else None,
                    model=self.deployment,
                    size=size,
                    quality=quality,
                )
            )
        return results


def _extract_response_data(response: Any) -> list[Any]:
    data = _get_value(response, "data")
    if not isinstance(data, list):
        raise ValueError("Image generation response did not include a data list")
    return data


def _get_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)
