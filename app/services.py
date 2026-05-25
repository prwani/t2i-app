"""Shared Streamlit app services."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from t2i_core import EvaluationPipeline, GPTImageProvider, MAIImageProvider, Settings
from t2i_core.clients import get_openai_client
from t2i_core.evaluation.openai_json import create_json_chat_completion
from t2i_core.providers.base import ImageProvider
from t2i_core.scenarios import (
    BrandTemplate,
    adapt_aspect_ratios,
    compose_images,
    generate_brand_asset,
    generate_ranked_variations,
    generate_text_rendering,
    inpaint_image,
    place_product,
    refine_image_chain,
)
from t2i_core.types import EditResult, EvaluationReport, GenerationResult


ImageModel = Literal["gpt-image-2", "MAI-Image-2", "MAI-Image-2e"]
LayerName = Literal["embedding", "rubric", "judge"]

PROMPT_ENHANCEMENT_INSTRUCTIONS = """You improve prompts for image generation and editing workflows.
Apply production image-prompting best practices:
- Keep the user's intent and do not add unrelated objects, logos, brands, or claims.
- Structure the prompt clearly: intended use, scene/background, subject, key details, style or medium, composition/framing, lighting/mood, and constraints.
- Use concrete visual details for materials, textures, shapes, colors, camera/framing, and placement.
- For photorealistic prompts, explicitly include photorealistic or professional photography when appropriate.
- For text in images, put literal text in quotes and describe typography, hierarchy, size, color, placement, and contrast.
- For edits and source-image workflows, specify what to change and what to preserve.
- For multi-image composition, refer to inputs by index and role, such as Image 1: product photo, Image 2: background.
- Avoid overloading the prompt; produce one clear, maintainable prompt.
Respond with only this JSON object: {"enhanced_prompt":"..."}"""


@dataclass
class GeneratedAsset:
    """Generated image plus display metadata."""

    name: str
    result: GenerationResult | EditResult
    evaluation: EvaluationReport | None = None
    caption: str | None = None


def run_async(coro):
    """Run an async SDK operation from a Streamlit callback."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise RuntimeError("Streamlit app service cannot run inside an existing event loop")


def build_provider(settings: Settings, model: ImageModel) -> ImageProvider:
    if model == "gpt-image-2":
        return GPTImageProvider(settings)
    if model == "MAI-Image-2e":
        return MAIImageProvider(settings, deployment=settings.mai_image_efficient_deployment)
    return MAIImageProvider(settings, deployment=settings.mai_image_deployment)


async def improve_prompt_with_ai(prompt: str, scenario: str) -> str:
    """Improve an image prompt with the configured Azure OpenAI text model."""

    cleaned = prompt.strip()
    if not cleaned:
        raise ValueError("Enter a prompt before improving it")
    settings = Settings()
    client = get_openai_client(settings)
    model_config = settings.eval_model_config
    try:
        payload, _ = await create_json_chat_completion(
            client,
            model=model_config.judge_deployment,
            is_o_series=model_config.judge_is_o_series,
            instructions=PROMPT_ENHANCEMENT_INSTRUCTIONS,
            user_content=(
                f"Scenario: {scenario}\n"
                f"Current prompt:\n{cleaned}\n\n"
                "Improve this prompt for the selected image workflow. Return JSON only."
            ),
            max_tokens=1200,
        )
    finally:
        await client.close()
    enhanced = payload.get("enhanced_prompt")
    if not isinstance(enhanced, str) or not enhanced.strip():
        raise ValueError("Prompt enhancer did not return enhanced_prompt")
    return enhanced.strip()


async def generate_images(
    prompt: str,
    model: ImageModel,
    *,
    size: str,
    quality: str,
    n: int,
) -> list[GeneratedAsset]:
    settings = Settings()
    provider = build_provider(settings, model)
    try:
        results = await provider.generate(prompt, size=size, quality=quality, n=n)
        return [
            GeneratedAsset(name=f"{model}-{index}.png", result=result)
            for index, result in enumerate(results, start=1)
        ]
    finally:
        await close_provider(provider)


async def generate_aspect_package(
    prompt: str,
    model: ImageModel,
    formats: list[str],
    *,
    quality: str,
) -> list[GeneratedAsset]:
    settings = Settings()
    provider = build_provider(settings, model)
    try:
        adapted = await adapt_aspect_ratios(provider, prompt, formats, quality=quality)
        return [
            GeneratedAsset(name=f"{item.target_format}.png", result=item.result)
            for item in adapted
        ]
    finally:
        await close_provider(provider)


async def generate_brand_template_assets(
    content_brief: str,
    model: ImageModel,
    *,
    colors: list[str],
    font_style: str,
    tone: str,
    logo_description: str | None,
    size: str,
    quality: str,
    n: int,
) -> list[GeneratedAsset]:
    settings = Settings()
    provider = build_provider(settings, model)
    brand = BrandTemplate(
        colors=colors,
        font_style=font_style,
        tone=tone,
        logo_description=logo_description,
    )
    try:
        results = await generate_brand_asset(
            provider,
            brand,
            content_brief,
            size=size,
            quality=quality,
            n=n,
        )
        return [
            GeneratedAsset(name=f"brand-{index}.png", result=result)
            for index, result in enumerate(results, start=1)
        ]
    finally:
        await close_provider(provider)


async def generate_text_rendering_assets(
    visual_prompt: str,
    model: ImageModel,
    *,
    text: str,
    size: str,
    quality: str,
    n: int,
) -> list[GeneratedAsset]:
    settings = Settings()
    provider = build_provider(settings, model)
    try:
        results = await generate_text_rendering(
            provider,
            text,
            visual_prompt,
            size=size,
            quality=quality,
            n=n,
        )
        return [
            GeneratedAsset(name=f"text-rendering-{index}.png", result=result)
            for index, result in enumerate(results, start=1)
        ]
    finally:
        await close_provider(provider)


async def compose_uploaded_images(
    images: list[bytes],
    prompt: str,
    *,
    size: str,
    quality: str,
) -> list[GeneratedAsset]:
    settings = Settings()
    provider = GPTImageProvider(settings)
    try:
        results = await compose_images(provider, images, prompt, size=size, quality=quality)
        return [
            GeneratedAsset(name=f"composition-{index}.png", result=result)
            for index, result in enumerate(results, start=1)
        ]
    finally:
        await provider.client.close()


async def inpaint_uploaded_image(
    image: bytes,
    prompt: str,
    *,
    mask: bytes | None,
    size: str,
    quality: str,
) -> list[GeneratedAsset]:
    settings = Settings()
    provider = GPTImageProvider(settings)
    try:
        results = await inpaint_image(
            provider,
            image,
            prompt,
            mask=mask,
            size=size,
            quality=quality,
        )
        return [
            GeneratedAsset(name=f"inpainting-{index}.png", result=result)
            for index, result in enumerate(results, start=1)
        ]
    finally:
        await provider.client.close()


async def place_product_assets(
    product_image: bytes,
    environments: list[str],
    *,
    size: str,
    quality: str,
) -> list[GeneratedAsset]:
    settings = Settings()
    provider = GPTImageProvider(settings)
    try:
        results = await place_product(
            provider,
            product_image,
            environments,
            size=size,
            quality=quality,
        )
        return [
            GeneratedAsset(
                name=f"product-placement-{index}.png",
                result=result,
                caption=environments[index - 1] if index - 1 < len(environments) else None,
            )
            for index, result in enumerate(results, start=1)
        ]
    finally:
        await provider.client.close()


async def refine_image_assets(
    initial_prompt: str,
    instructions: list[str],
    *,
    size: str,
    quality: str,
) -> list[GeneratedAsset]:
    settings = Settings()
    provider = GPTImageProvider(settings)
    try:
        chain = await refine_image_chain(
            provider,
            initial_prompt,
            instructions,
            size=size,
            quality=quality,
        )
        assets = [
            GeneratedAsset(
                name="refinement-0-initial.png",
                result=chain.initial,
                caption=f"Initial: {initial_prompt}",
            )
        ]
        assets.extend(
            GeneratedAsset(
                name=f"refinement-{index}.png",
                result=result,
                caption=f"Turn {index}: {instructions[index - 1]}",
            )
            for index, result in enumerate(chain.refinements, start=1)
        )
        return assets
    finally:
        await provider.client.close()


async def evaluate_image(
    image: bytes,
    prompt: str,
    layers: list[LayerName],
    *,
    model_used: str | None = None,
    image_path: str | None = None,
) -> EvaluationReport:
    settings = Settings()
    pipeline = EvaluationPipeline(settings)
    try:
        return await pipeline.evaluate(
            image,
            prompt,
            layers=layers,
            model_used=model_used,
            image_path=image_path,
        )
    finally:
        await pipeline.embedding.http_client.aclose()


async def generate_and_rank(
    prompt: str,
    *,
    n: int,
    quality: str,
    layers: list[LayerName],
) -> list[GeneratedAsset]:
    settings = Settings()
    provider = GPTImageProvider(settings)
    pipeline = EvaluationPipeline(settings)
    try:
        ranked = await generate_ranked_variations(
            provider,
            prompt,
            n=n,
            quality=quality,
            pipeline=pipeline,
            layers=layers,
        )
        return [
            GeneratedAsset(
                name=f"rank-{item.rank}.png",
                result=item.generation,
                evaluation=item.evaluation,
            )
            for item in ranked
        ]
    finally:
        await pipeline.embedding.http_client.aclose()
        await provider.client.close()


async def close_provider(provider: ImageProvider) -> None:
    if hasattr(provider, "client"):
        await provider.client.close()
    if hasattr(provider, "aclose"):
        await provider.aclose()


def save_asset(asset: GeneratedAsset, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / asset.name
    path.write_bytes(asset.result.image)
    return path
