import base64

import pytest

from t2i_core.utils import (
    ImageValidationError,
    decode_base64_image,
    encode_base64_image,
    trim_to_word_limit,
    validate_image_for_vision,
)


def test_base64_round_trip(png_bytes: bytes) -> None:
    encoded = encode_base64_image(png_bytes)

    assert decode_base64_image(encoded) == png_bytes


def test_decode_base64_data_url(png_bytes: bytes) -> None:
    encoded = base64.b64encode(png_bytes).decode("ascii")

    assert decode_base64_image(f"data:image/png;base64,{encoded}") == png_bytes


def test_validate_image_for_vision_accepts_valid_png(png_bytes: bytes) -> None:
    validate_image_for_vision(png_bytes)


def test_validate_image_for_vision_rejects_invalid_bytes() -> None:
    with pytest.raises(ImageValidationError, match="valid image"):
        validate_image_for_vision(b"not an image")


def test_trim_to_word_limit() -> None:
    assert trim_to_word_limit("one two three four", 2) == "one two"
