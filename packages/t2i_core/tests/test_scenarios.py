import pytest

from t2i_core.scenarios.aspect_ratio_adaptation import adapt_aspect_ratios
from t2i_core.scenarios.brand_template import BrandTemplate, compose_brand_prompt, generate_brand_asset
from t2i_core.scenarios.multi_image_composition import compose_images
from t2i_core.types import EditResult, GenerationResult


class FakeProvider:
    async def generate(self, prompt: str, size: str = "1024x1024", quality: str = "high", n: int = 1):
        return [
            GenerationResult(image=b"image", prompt=prompt, model="fake", size=size, quality=quality)
            for _ in range(n)
        ]

    async def edit(self, images: list[bytes], prompt: str, mask=None, **kwargs):
        return [
            EditResult(
                image=b"edited",
                prompt=prompt,
                model="fake",
                size=kwargs.get("size", "1024x1024"),
                quality=kwargs.get("quality", "high"),
                source_image_count=len(images),
                mask_used=mask is not None,
            )
        ]


def test_compose_brand_prompt_includes_constraints() -> None:
    prompt = compose_brand_prompt(
        BrandTemplate(colors=["#0078D4"], font_style="modern", tone="professional"),
        "launch banner",
    )

    assert "#0078D4" in prompt
    assert "launch banner" in prompt


@pytest.mark.asyncio
async def test_brand_generation_uses_composed_prompt() -> None:
    result = await generate_brand_asset(
        FakeProvider(),  # type: ignore[arg-type]
        BrandTemplate(colors=["blue"], font_style="modern", tone="friendly"),
        "hero image",
    )

    assert "hero image" in result[0].prompt


@pytest.mark.asyncio
async def test_composition_requires_multiple_images() -> None:
    with pytest.raises(ValueError, match="2 to 16"):
        await compose_images(FakeProvider(), [b"one"], "combine")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_aspect_ratio_maps_to_supported_api_sizes() -> None:
    results = await adapt_aspect_ratios(
        FakeProvider(),  # type: ignore[arg-type]
        "product hero",
        ["desktop_hero", "mobile_story"],
    )

    assert [result.api_size for result in results] == ["1536x1024", "1024x1536"]
