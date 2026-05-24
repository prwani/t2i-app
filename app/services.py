"""Shared Streamlit app services."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from t2i_core import EvaluationPipeline, GPTImageProvider, MAIImageProvider, Settings
from t2i_core.providers.base import ImageProvider
from t2i_core.scenarios import adapt_aspect_ratios, generate_ranked_variations
from t2i_core.types import EvaluationReport, GenerationResult


ImageModel = Literal["gpt-image-2", "MAI-Image-2", "MAI-Image-2e"]
LayerName = Literal["embedding", "rubric", "judge"]


@dataclass
class GeneratedAsset:
    """Generated image plus display metadata."""

    name: str
    result: GenerationResult


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
            GeneratedAsset(name=f"rank-{item.rank}.png", result=item.generation)
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
