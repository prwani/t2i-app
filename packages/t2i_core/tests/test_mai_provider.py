import base64

import pytest
from httpx import Request, Response

from t2i_core.providers.mai_image import MAIImageProvider


class FakeHTTPClient:
    def __init__(self, image: bytes) -> None:
        self.image = image
        self.url = None
        self.params = None
        self.headers = None
        self.json = None
        self.data = None
        self.files = None

    async def post(self, url, *, params, headers, json=None, data=None, files=None):
        self.url = url
        self.params = params
        self.headers = headers
        self.json = json
        self.data = data
        self.files = files
        return Response(
            200,
            request=Request("POST", url),
            json={
                "data": [
                    {
                        "b64_json": base64.b64encode(self.image).decode("ascii"),
                        "revised_prompt": "revised",
                    }
                ]
            },
        )

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_mai_provider_decodes_b64_response(settings, png_bytes: bytes) -> None:
    client = FakeHTTPClient(png_bytes)
    provider = MAIImageProvider(
        settings=settings,
        http_client=client,  # type: ignore[arg-type]
        token_provider=lambda: "fake-token",
    )

    results = await provider.generate("red square", n=1)

    assert results[0].image == png_bytes
    assert results[0].revised_prompt == "revised"
    assert client.url == "https://example-openai.services.ai.azure.com/mai/v1/images/generations"
    assert client.params == {"api-version": "preview"}
    assert client.headers["Authorization"] == "Bearer fake-token"
    assert client.json == {
        "model": "MAI-Image-2",
        "prompt": "red square",
        "width": 1024,
        "height": 1024,
        "n": 1,
    }


@pytest.mark.asyncio
async def test_mai_provider_sends_edit_request(settings, png_bytes: bytes) -> None:
    client = FakeHTTPClient(png_bytes)
    provider = MAIImageProvider(
        settings=settings,
        deployment="MAI-Image-2.5",
        http_client=client,  # type: ignore[arg-type]
        token_provider=lambda: "fake-token",
    )

    results = await provider.edit([png_bytes], "make this a studio shot", mask=png_bytes)

    assert results[0].image == png_bytes
    assert results[0].model == "MAI-Image-2.5"
    assert results[0].source_image_count == 1
    assert results[0].mask_used is True
    assert client.url == "https://example-openai.services.ai.azure.com/mai/v1/images/edits"
    assert client.params == {"api-version": "preview"}
    assert client.headers["Authorization"] == "Bearer fake-token"
    assert client.data == {"model": "MAI-Image-2.5", "prompt": "make this a studio shot"}
    assert client.files == [
        ("image", ("image.png", png_bytes, "image/png")),
        ("mask", ("mask.png", png_bytes, "image/png")),
    ]


@pytest.mark.asyncio
async def test_mai_provider_rejects_edit_for_generation_only_deployment(settings, png_bytes: bytes) -> None:
    provider = MAIImageProvider(
        settings=settings,
        deployment="MAI-Image-2e",
        http_client=FakeHTTPClient(png_bytes),  # type: ignore[arg-type]
        token_provider=lambda: "fake-token",
    )

    with pytest.raises(ValueError, match="does not support image-to-image edits"):
        await provider.edit([png_bytes], "edit")
