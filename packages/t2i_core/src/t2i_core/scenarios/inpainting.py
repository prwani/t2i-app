"""Inpainting and selective editing scenario."""

from t2i_core.providers.base import EditableImageProvider
from t2i_core.types import EditResult


async def inpaint_image(
    provider: EditableImageProvider,
    image: bytes,
    edit_prompt: str,
    *,
    mask: bytes | None = None,
    size: str = "1024x1024",
    quality: str = "high",
) -> list[EditResult]:
    """Edit a source image, optionally constrained by a transparent-mask region."""

    return await provider.edit([image], edit_prompt, mask=mask, size=size, quality=quality)
