"""Shared utility helpers."""

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image


DATA_URL_SEPARATOR = ";base64,"
MAX_VISION_IMAGE_BYTES = 20 * 1024 * 1024
MIN_VISION_IMAGE_DIMENSION = 10
MAX_VISION_IMAGE_DIMENSION = 16_000


class ImageValidationError(ValueError):
    """Raised when an image cannot be sent to Azure AI Vision."""


def decode_base64_image(data: str) -> bytes:
    """Decode plain base64 or a data URL into bytes."""

    payload = data.split(DATA_URL_SEPARATOR, 1)[1] if DATA_URL_SEPARATOR in data else data
    return base64.b64decode(payload, validate=True)


def encode_base64_image(image: bytes) -> str:
    """Encode bytes as base64 text."""

    return base64.b64encode(image).decode("ascii")


def read_image(path: str | Path) -> bytes:
    """Read image bytes from disk."""

    return Path(path).read_bytes()


def write_bytes(path: str | Path, data: bytes) -> Path:
    """Write bytes to disk and return the resolved path."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return output


def validate_image_for_vision(image: bytes) -> None:
    """Validate Azure AI Vision vectorization image constraints."""

    if len(image) > MAX_VISION_IMAGE_BYTES:
        raise ImageValidationError("Azure AI Vision images must be smaller than 20 MB")

    try:
        with Image.open(BytesIO(image)) as parsed:
            width, height = parsed.size
    except Exception as exc:  # Pillow raises several exception types for invalid image data.
        raise ImageValidationError("Image bytes must be a valid image") from exc

    if width <= MIN_VISION_IMAGE_DIMENSION or height <= MIN_VISION_IMAGE_DIMENSION:
        raise ImageValidationError("Azure AI Vision images must be larger than 10x10 pixels")
    if width >= MAX_VISION_IMAGE_DIMENSION or height >= MAX_VISION_IMAGE_DIMENSION:
        raise ImageValidationError("Azure AI Vision images must be smaller than 16000x16000 pixels")


def count_words(text: str) -> int:
    """Count whitespace-delimited words."""

    return len(text.split())


def trim_to_word_limit(text: str, word_limit: int) -> str:
    """Trim text to a maximum number of whitespace-delimited words."""

    words = text.split()
    if len(words) <= word_limit:
        return text
    return " ".join(words[:word_limit])
