import base64
from types import SimpleNamespace

import pytest

from t2i_core.providers.mai_image import MAIImageProvider


class FakeImages:
    def __init__(self, image: bytes) -> None:
        self.image = image
        self.kwargs = None

    async def generate(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            data=[
                SimpleNamespace(
                    b64_json=base64.b64encode(self.image).decode("ascii"),
                    revised_prompt="revised",
                )
            ]
        )


class FakeClient:
    def __init__(self, image: bytes) -> None:
        self.images = FakeImages(image)


@pytest.mark.asyncio
async def test_mai_provider_decodes_b64_response(settings, png_bytes: bytes) -> None:
    client = FakeClient(png_bytes)
    provider = MAIImageProvider(settings=settings, client=client)  # type: ignore[arg-type]

    results = await provider.generate("red square", n=1)

    assert results[0].image == png_bytes
    assert results[0].revised_prompt == "revised"
    assert client.images.kwargs == {
        "model": "mai-image-2",
        "prompt": "red square",
        "n": 1,
        "size": "1024x1024",
        "quality": "high",
        "output_format": "png",
    }
