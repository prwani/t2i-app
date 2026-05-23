"""Multi-image composition scenario."""

from t2i_core.providers.base import EditableImageProvider
from t2i_core.types import EditResult


async def compose_images(
    provider: EditableImageProvider,
    images: list[bytes],
    composition_prompt: str,
    *,
    size: str = "1024x1024",
    quality: str = "high",
) -> list[EditResult]:
    """Compose 2-16 source images into a new image."""

    if not 2 <= len(images) <= 16:
        raise ValueError("multi-image composition requires 2 to 16 images")
    return await provider.edit(images, composition_prompt, size=size, quality=quality)
