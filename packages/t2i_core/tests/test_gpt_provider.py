import base64
from io import BytesIO
from types import SimpleNamespace

import pytest
from httpx import Request, Response
from openai import APIStatusError
from PIL import Image

from t2i_core.providers.gpt_image import GPTImageProvider
from t2i_core.utils import ImageValidationError


class FakeImages:
    def __init__(self, image: bytes) -> None:
        self.image = image
        self.generate_kwargs = None
        self.edit_kwargs = None

    async def generate(self, **kwargs):
        self.generate_kwargs = kwargs
        return _image_response(self.image)

    async def edit(self, **kwargs):
        self.edit_kwargs = kwargs
        return _image_response(self.image)


class FakeClient:
    def __init__(self, image: bytes) -> None:
        self.images = FakeImages(image)


class RetryFakeImages(FakeImages):
    def __init__(self, image: bytes) -> None:
        super().__init__(image)
        self.edit_calls = 0

    async def edit(self, **kwargs):
        self.edit_calls += 1
        if self.edit_calls == 1:
            request = Request("POST", "https://example.openai.azure.com/openai/v1/images/edits")
            response = Response(
                408,
                request=request,
                json={"error": {"code": "Timeout", "message": "The operation was timeout."}},
            )
            raise APIStatusError("timeout", response=response, body=response.json())
        return await super().edit(**kwargs)


class RetryFakeClient:
    def __init__(self, image: bytes) -> None:
        self.images = RetryFakeImages(image)


def _image_response(image: bytes):
    return SimpleNamespace(
        data=[
            SimpleNamespace(
                b64_json=base64.b64encode(image).decode("ascii"),
                revised_prompt="revised",
            )
        ],
        usage=SimpleNamespace(input_tokens=12, output_tokens=34),
    )


def _rgba_mask(size: tuple[int, int]) -> bytes:
    output = BytesIO()
    Image.new("RGBA", size, color=(0, 0, 0, 0)).save(output, format="PNG")
    return output.getvalue()


@pytest.mark.asyncio
async def test_gpt_provider_generates_and_tracks_usage(settings, png_bytes: bytes) -> None:
    client = FakeClient(png_bytes)
    provider = GPTImageProvider(settings=settings, client=client)  # type: ignore[arg-type]

    results = await provider.generate("red square", n=1)

    assert results[0].image == png_bytes
    assert results[0].usage.input_tokens == 12
    assert client.images.generate_kwargs["model"] == "gpt-image-2"
    assert client.images.generate_kwargs["background"] == "auto"


@pytest.mark.asyncio
async def test_gpt_provider_edits_with_multiple_images_and_mask(settings, png_bytes: bytes) -> None:
    client = FakeClient(png_bytes)
    provider = GPTImageProvider(settings=settings, client=client)  # type: ignore[arg-type]

    results = await provider.edit([png_bytes, png_bytes], "combine them", mask=_rgba_mask((16, 16)))

    assert results[0].source_image_count == 2
    assert results[0].mask_used is True
    assert len(client.images.edit_kwargs["image"]) == 2
    assert client.images.edit_kwargs["mask"][0] == "mask.png"


@pytest.mark.asyncio
async def test_gpt_provider_rejects_mask_without_alpha(settings, png_bytes: bytes) -> None:
    client = FakeClient(png_bytes)
    provider = GPTImageProvider(settings=settings, client=client)  # type: ignore[arg-type]

    with pytest.raises(ImageValidationError, match="alpha"):
        await provider.edit([png_bytes], "edit", mask=png_bytes)


@pytest.mark.asyncio
async def test_gpt_provider_retries_transient_edit_timeout(settings, png_bytes: bytes) -> None:
    client = RetryFakeClient(png_bytes)
    provider = GPTImageProvider(
        settings=settings,
        client=client,  # type: ignore[arg-type]
        max_retries=1,
        retry_delay_seconds=0,
    )

    results = await provider.edit([png_bytes], "edit", mask=_rgba_mask((16, 16)))

    assert results[0].image == png_bytes
    assert client.images.edit_calls == 2
