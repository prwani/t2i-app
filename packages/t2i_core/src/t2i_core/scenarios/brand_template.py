"""Brand-template image generation scenario."""

from pydantic import BaseModel, Field

from t2i_core.providers.base import ImageProvider
from t2i_core.types import GenerationResult


class BrandTemplate(BaseModel):
    """Reusable visual brand constraints."""

    colors: list[str] = Field(min_length=1)
    font_style: str
    tone: str
    logo_description: str | None = None


def compose_brand_prompt(brand: BrandTemplate, content_brief: str) -> str:
    """Compose a generation prompt with brand constraints."""

    parts = [
        f"Create an on-brand marketing image. Content brief: {content_brief.strip()}",
        f"Brand colors: {', '.join(brand.colors)}.",
        f"Typography style: {brand.font_style}.",
        f"Tone: {brand.tone}.",
    ]
    if brand.logo_description:
        parts.append(f"Include or leave space for this logo concept: {brand.logo_description}.")
    return " ".join(parts)


async def generate_brand_asset(
    provider: ImageProvider,
    brand: BrandTemplate,
    content_brief: str,
    *,
    size: str = "1024x1024",
    quality: str = "high",
    n: int = 1,
) -> list[GenerationResult]:
    """Generate brand-constrained image assets."""

    return await provider.generate(compose_brand_prompt(brand, content_brief), size=size, quality=quality, n=n)
