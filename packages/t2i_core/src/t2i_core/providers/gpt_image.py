"""GPT image provider."""

import asyncio
from io import BytesIO
from collections.abc import Awaitable, Callable
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from PIL import Image

from t2i_core.clients import get_openai_client
from t2i_core.providers.base import EditableImageProvider
from t2i_core.settings import Settings
from t2i_core.types import EditResult, GenerationResult, UsageCost
from t2i_core.utils import ImageValidationError, decode_base64_image


MAX_EDIT_IMAGES = 16
MAX_EDIT_IMAGE_BYTES = 25 * 1024 * 1024
TRANSIENT_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


class GPTImageProvider(EditableImageProvider):
    """Provider for GPT-Image deployments using Azure OpenAI image APIs."""

    def __init__(
        self,
        settings: Settings,
        client: AsyncOpenAI | None = None,
        deployment: str | None = None,
        max_retries: int = 2,
        retry_delay_seconds: float = 2.0,
    ) -> None:
        self.settings = settings
        self.client = client or get_openai_client(settings)
        self.deployment = deployment or settings.gpt_image_deployment
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1,
        background: str = "auto",
    ) -> list[GenerationResult]:
        """Generate one or more images from a text prompt."""

        response = await _with_transient_retries(
            lambda: self.client.images.generate(
                model=self.deployment,
                prompt=prompt,
                n=n,
                size=size,
                quality=quality,
                output_format="png",
                background=background,
            ),
            max_retries=self.max_retries,
            retry_delay_seconds=self.retry_delay_seconds,
        )
        return [
            GenerationResult(
                image=decode_base64_image(_required_b64(item)),
                prompt=prompt,
                revised_prompt=_optional_str(item, "revised_prompt"),
                model=self.deployment,
                size=size,
                quality=quality,
                usage=_extract_usage(response),
            )
            for item in _extract_response_data(response)
        ]

    async def edit(
        self,
        images: list[bytes],
        prompt: str,
        mask: bytes | None = None,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1,
        background: str = "auto",
        input_fidelity: str = "high",
    ) -> list[EditResult]:
        """Edit, inpaint, or compose images."""

        image_sizes = [_validate_edit_image(image, f"image[{index}]") for index, image in enumerate(images)]
        if not image_sizes:
            raise ValueError("at least one image is required for editing")
        if len(image_sizes) > MAX_EDIT_IMAGES:
            raise ValueError(f"no more than {MAX_EDIT_IMAGES} images can be edited at once")
        if mask is not None:
            _validate_mask(mask, image_sizes[0])

        async def call_edit():
            files = [
                (f"image_{index}.png", BytesIO(image), "image/png")
                for index, image in enumerate(images)
            ]
            mask_file = ("mask.png", BytesIO(mask), "image/png") if mask is not None else None
            kwargs: dict[str, Any] = {
                "model": self.deployment,
                "image": files,
                "prompt": prompt,
                "n": n,
                "size": size,
                "quality": quality,
                "output_format": "png",
                "background": background,
                "input_fidelity": input_fidelity,
            }
            if mask_file is not None:
                kwargs["mask"] = mask_file
            return await self.client.images.edit(**kwargs)

        response = await _with_transient_retries(
            call_edit,
            max_retries=self.max_retries,
            retry_delay_seconds=self.retry_delay_seconds,
        )
        return [
            EditResult(
                image=decode_base64_image(_required_b64(item)),
                prompt=prompt,
                revised_prompt=_optional_str(item, "revised_prompt"),
                model=self.deployment,
                size=size,
                quality=quality,
                source_image_count=len(images),
                mask_used=mask is not None,
                usage=_extract_usage(response),
            )
            for item in _extract_response_data(response)
        ]


def _extract_response_data(response: Any) -> list[Any]:
    data = _get_value(response, "data")
    if not isinstance(data, list):
        raise ValueError("Image response did not include a data list")
    return data


async def _with_transient_retries(
    operation: Callable[[], Awaitable[Any]],
    *,
    max_retries: int,
    retry_delay_seconds: float,
) -> Any:
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except (APIConnectionError, APITimeoutError) as exc:
            if attempt >= max_retries:
                raise
            await asyncio.sleep(retry_delay_seconds * (attempt + 1))
        except APIStatusError as exc:
            if exc.status_code not in TRANSIENT_STATUS_CODES or attempt >= max_retries:
                raise
            await asyncio.sleep(retry_delay_seconds * (attempt + 1))


def _required_b64(item: Any) -> str:
    b64_json = _get_value(item, "b64_json")
    if not isinstance(b64_json, str) or not b64_json:
        raise ValueError("Image response did not include b64_json")
    return b64_json


def _optional_str(item: Any, key: str) -> str | None:
    value = _get_value(item, key)
    return value if isinstance(value, str) else None


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


def _validate_edit_image(image: bytes, label: str) -> tuple[int, int]:
    if len(image) > MAX_EDIT_IMAGE_BYTES:
        raise ImageValidationError(f"{label} must be 25 MB or smaller")
    try:
        with Image.open(BytesIO(image)) as parsed:
            parsed.verify()
        with Image.open(BytesIO(image)) as parsed:
            return parsed.size
    except Exception as exc:
        raise ImageValidationError(f"{label} must be a valid image") from exc


def _validate_mask(mask: bytes, source_size: tuple[int, int]) -> None:
    if len(mask) > MAX_EDIT_IMAGE_BYTES:
        raise ImageValidationError("mask must be 25 MB or smaller")
    try:
        with Image.open(BytesIO(mask)) as parsed:
            if parsed.format != "PNG":
                raise ImageValidationError("mask must be a PNG image")
            if parsed.size != source_size:
                raise ImageValidationError("mask dimensions must match the first source image")
            if "A" not in parsed.getbands():
                raise ImageValidationError("mask must include an alpha channel")
    except ImageValidationError:
        raise
    except Exception as exc:
        raise ImageValidationError("mask must be a valid PNG image") from exc
