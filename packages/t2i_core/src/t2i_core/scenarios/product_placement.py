"""Product placement image scenario."""

from t2i_core.providers.base import EditableImageProvider
from t2i_core.types import EditResult


async def place_product(
    provider: EditableImageProvider,
    product_image: bytes,
    environments: list[str],
    *,
    size: str = "1024x1024",
    quality: str = "high",
) -> list[EditResult]:
    """Place one product image into multiple environment prompts."""

    if not environments:
        raise ValueError("at least one environment description is required")
    results: list[EditResult] = []
    for environment in environments:
        prompt = f"Place this product naturally in the following environment: {environment}"
        results.extend(await provider.edit([product_image], prompt, size=size, quality=quality, n=1))
    return results
