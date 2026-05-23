"""Aspect ratio adaptation scenario."""

from pydantic import BaseModel

from t2i_core.providers.base import ImageProvider
from t2i_core.types import GenerationResult


SUPPORTED_FORMAT_SIZES = {
    "instagram_square": "1024x1024",
    "instagram_story": "1024x1536",
    "linkedin_banner": "1536x1024",
    "desktop_hero": "1536x1024",
    "mobile_story": "1024x1536",
}


class AdaptedImage(BaseModel):
    """Generated image for a requested target format."""

    target_format: str
    api_size: str
    result: GenerationResult


async def adapt_aspect_ratios(
    provider: ImageProvider,
    concept_prompt: str,
    formats: list[str],
    *,
    quality: str = "high",
) -> list[AdaptedImage]:
    """Generate one API-supported image size for each target format."""

    if not formats:
        raise ValueError("at least one target format is required")
    adapted: list[AdaptedImage] = []
    for target_format in formats:
        try:
            size = SUPPORTED_FORMAT_SIZES[target_format]
        except KeyError as exc:
            raise ValueError(f"unsupported target format: {target_format}") from exc
        prompt = f"{concept_prompt.strip()} Compose for {target_format.replace('_', ' ')}."
        result = (await provider.generate(prompt, size=size, quality=quality, n=1))[0]
        adapted.append(AdaptedImage(target_format=target_format, api_size=size, result=result))
    return adapted
