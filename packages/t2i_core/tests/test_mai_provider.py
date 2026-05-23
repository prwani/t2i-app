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

    async def post(self, url, *, params, headers, json):
        self.url = url
        self.params = params
        self.headers = headers
        self.json = json
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
        "model": "mai-image-2",
        "prompt": "red square",
        "width": 1024,
        "height": 1024,
        "n": 1,
    }
