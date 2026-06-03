"""MAI image provider."""

from typing import Any

import httpx

from t2i_core.clients import get_http_client, get_openai_token_provider
from t2i_core.providers.base import EditableImageProvider
from t2i_core.settings import Settings
from t2i_core.types import EditResult, GenerationResult, UsageCost
from t2i_core.utils import decode_base64_image


EDIT_CAPABLE_DEPLOYMENTS = {"MAI-Image-2.5-Flash", "MAI-Image-2.5"}


class MAIImageProvider(EditableImageProvider):
    """Provider for MAI-Image deployments using the Foundry MAI image API."""

    def __init__(
        self,
        settings: Settings,
        http_client: httpx.AsyncClient | None = None,
        token_provider: Any | None = None,
        deployment: str | None = None,
    ) -> None:
        self.settings = settings
        self.http_client = http_client or get_http_client(timeout=300.0)
        self.token_provider = token_provider or get_openai_token_provider(settings)
        self.deployment = deployment or settings.mai_image_deployment

    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1,
    ) -> list[GenerationResult]:
        """Generate image bytes from a text prompt."""

        width, height = _parse_size(size)
        response = await self.http_client.post(
            f"{self.settings.foundry_services_endpoint}/mai/v1/images/generations",
            params={"api-version": "preview"},
            headers={
                "Authorization": f"Bearer {self.token_provider()}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.deployment,
                "prompt": prompt,
                "width": width,
                "height": height,
                "n": n,
            },
        )
        response.raise_for_status()

        payload = response.json()
        data = _extract_response_data(payload)
        usage = _extract_usage(payload)
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
                    usage=usage,
                )
            )
        return results

    async def edit(
        self,
        images: list[bytes],
        prompt: str,
        mask: bytes | None = None,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1,
        **kwargs: object,
    ) -> list[EditResult]:
        """Edit one source image with MAI-Image-2.5 models."""

        if self.deployment not in EDIT_CAPABLE_DEPLOYMENTS:
            raise ValueError(f"{self.deployment} does not support image-to-image edits")
        if len(images) != 1:
            raise ValueError("MAI image edits require exactly one source image")
        if n < 1:
            raise ValueError("n must be at least 1")

        results: list[EditResult] = []
        for _ in range(n):
            response = await self.http_client.post(
                f"{self.settings.foundry_services_endpoint}/mai/v1/images/edits",
                params={"api-version": "preview"},
                headers={
                    "Authorization": f"Bearer {self.token_provider()}",
                },
                data={
                    "model": self.deployment,
                    "prompt": prompt,
                },
                files=_edit_files(images[0], mask),
            )
            response.raise_for_status()
            payload = response.json()
            usage = _extract_usage(payload)
            for item in _extract_response_data(payload):
                b64_json = _get_value(item, "b64_json")
                if not isinstance(b64_json, str) or not b64_json:
                    raise ValueError("Image edit response did not include b64_json")
                revised_prompt = _get_value(item, "revised_prompt")
                results.append(
                    EditResult(
                        image=decode_base64_image(b64_json),
                        prompt=prompt,
                        revised_prompt=revised_prompt if isinstance(revised_prompt, str) else None,
                        model=self.deployment,
                        size=size,
                        quality=quality,
                        source_image_count=1,
                        mask_used=mask is not None,
                        usage=usage,
                    )
                )
        return results

    async def aclose(self) -> None:
        """Close the internally managed HTTP client."""

        await self.http_client.aclose()


def _extract_response_data(response: Any) -> list[Any]:
    data = _get_value(response, "data")
    if not isinstance(data, list):
        raise ValueError("Image generation response did not include a data list")
    return data


def _get_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _extract_usage(response: Any) -> UsageCost:
    usage = _get_value(response, "usage")
    if usage is None:
        return UsageCost()
    input_tokens = _get_value(usage, "input_tokens")
    output_tokens = _get_value(usage, "output_tokens")
    return UsageCost(
        input_tokens=input_tokens if isinstance(input_tokens, int) else None,
        output_tokens=output_tokens if isinstance(output_tokens, int) else None,
    )


def _edit_files(image: bytes, mask: bytes | None) -> list[tuple[str, tuple[str, bytes, str]]]:
    files = [("image", ("image.png", image, "image/png"))]
    if mask is not None:
        files.append(("mask", ("mask.png", mask, "image/png")))
    return files


def _parse_size(size: str) -> tuple[int, int]:
    parts = size.lower().split("x", 1)
    if len(parts) != 2:
        raise ValueError("size must use WIDTHxHEIGHT format")
    try:
        width, height = (int(part) for part in parts)
    except ValueError as exc:
        raise ValueError("size must use numeric WIDTHxHEIGHT format") from exc
    if width <= 0 or height <= 0:
        raise ValueError("size dimensions must be positive")
    return width, height
