from io import BytesIO

import pytest
from PIL import Image

from t2i_core.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        AZURE_OPENAI_ENDPOINT="https://example-openai.openai.azure.com/",
        AZURE_VISION_ENDPOINT="https://example-vision.cognitiveservices.azure.com/",
    )


@pytest.fixture
def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (16, 16), color=(255, 0, 0)).save(output, format="PNG")
    return output.getvalue()
