"""Text rendering image scenario."""

from t2i_core.providers.base import ImageProvider
from t2i_core.types import GenerationResult


async def generate_text_rendering(
    provider: ImageProvider,
    text: str,
    visual_prompt: str,
    *,
    size: str = "1024x1024",
    quality: str = "high",
    n: int = 1,
) -> list[GenerationResult]:
    """Generate images that include exact visible text."""

    prompt = (
        f"Create an image with the exact readable text: {text!r}. "
        f"Visual context: {visual_prompt.strip()}. Prioritize text legibility and spelling accuracy."
    )
    return await provider.generate(prompt, size=size, quality=quality, n=n)
