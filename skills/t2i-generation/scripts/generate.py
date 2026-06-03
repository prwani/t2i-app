#!/usr/bin/env python3
"""CLI for image generation scenarios."""

import argparse
import asyncio
import json
from pathlib import Path

from t2i_core import GPTImageProvider, MAIImageProvider, Settings
from t2i_core.providers.base import ImageProvider
from t2i_core.scenarios import (
    BrandTemplate,
    adapt_aspect_ratios,
    compose_images,
    generate_brand_asset,
    generate_text_rendering,
    inpaint_image,
    place_product,
)
from t2i_core.utils import read_image, write_bytes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or edit images with t2i_core.")
    parser.add_argument("--scenario", required=True, choices=[
        "text",
        "brand-template",
        "text-rendering",
        "aspect-ratio",
        "inpainting",
        "composition",
        "product-placement",
    ])
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--model",
        default="gpt-image-2",
        choices=[
            "gpt-image-2",
            "mai-image-2",
            "mai-image-2e",
            "mai-image-2.5-flash",
            "mai-image-2.5",
            "MAI-Image-2",
            "MAI-Image-2e",
            "MAI-Image-2.5-Flash",
            "MAI-Image-2.5",
        ],
    )
    parser.add_argument("--image", action="append", default=[], help="Input image path; repeat for multiple images.")
    parser.add_argument("--mask", help="Optional PNG alpha mask for inpainting.")
    parser.add_argument("--brand-config", help="BrandTemplate JSON file.")
    parser.add_argument("--text", help="Exact text for text-rendering scenario.")
    parser.add_argument("--formats", default="instagram_square", help="Comma-separated aspect-ratio formats.")
    parser.add_argument("--environment", action="append", default=[], help="Environment for product placement.")
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--output", default="output.png")
    parser.add_argument("--output-dir", default="outputs")
    return parser.parse_args()


def build_provider(settings: Settings, model: str) -> ImageProvider:
    if model == "gpt-image-2":
        return GPTImageProvider(settings)
    if model in {"mai-image-2e", "MAI-Image-2e"}:
        return MAIImageProvider(settings, deployment=settings.mai_image_efficient_deployment)
    if model in {"mai-image-2.5-flash", "MAI-Image-2.5-Flash"}:
        return MAIImageProvider(settings, deployment=settings.mai_image_25_flash_deployment)
    if model in {"mai-image-2.5", "MAI-Image-2.5"}:
        return MAIImageProvider(settings, deployment=settings.mai_image_25_deployment)
    return MAIImageProvider(settings, deployment=settings.mai_image_deployment)


async def main() -> None:
    args = parse_args()
    settings = Settings()
    provider = build_provider(settings, args.model)

    try:
        if args.scenario == "text":
            results = await provider.generate(args.prompt, size=args.size, quality=args.quality, n=args.n)
            _write_generation_results(results, Path(args.output), Path(args.output_dir))
        elif args.scenario == "brand-template":
            if not args.brand_config:
                raise ValueError("--brand-config is required for brand-template")
            brand = BrandTemplate.model_validate_json(Path(args.brand_config).read_text(encoding="utf-8"))
            results = await generate_brand_asset(provider, brand, args.prompt, size=args.size, quality=args.quality, n=args.n)
            _write_generation_results(results, Path(args.output), Path(args.output_dir))
        elif args.scenario == "text-rendering":
            text = args.text or args.prompt
            results = await generate_text_rendering(provider, text, args.prompt, size=args.size, quality=args.quality, n=args.n)
            _write_generation_results(results, Path(args.output), Path(args.output_dir))
        elif args.scenario == "aspect-ratio":
            adapted = await adapt_aspect_ratios(provider, args.prompt, args.formats.split(","), quality=args.quality)
            output_dir = Path(args.output_dir)
            for item in adapted:
                path = write_bytes(output_dir / f"{item.target_format}.png", item.result.image)
                print(path)
        elif args.scenario == "inpainting":
            _require_gpt_provider(provider, args.scenario)
            if not args.image:
                raise ValueError("--image is required for inpainting")
            results = await inpaint_image(
                provider,
                read_image(args.image[0]),
                args.prompt,
                mask=read_image(args.mask) if args.mask else None,
                size=args.size,
                quality=args.quality,
            )
            _write_generation_results(results, Path(args.output), Path(args.output_dir))
        elif args.scenario == "composition":
            _require_gpt_provider(provider, args.scenario)
            results = await compose_images(
                provider,
                [read_image(path) for path in args.image],
                args.prompt,
                size=args.size,
                quality=args.quality,
            )
            _write_generation_results(results, Path(args.output), Path(args.output_dir))
        elif args.scenario == "product-placement":
            _require_gpt_provider(provider, args.scenario)
            if not args.image:
                raise ValueError("--image is required for product-placement")
            environments = args.environment or [args.prompt]
            results = await place_product(
                provider,
                read_image(args.image[0]),
                environments,
                size=args.size,
                quality=args.quality,
            )
            _write_generation_results(results, Path(args.output), Path(args.output_dir))
    finally:
        if hasattr(provider, "client"):
            await provider.client.close()
        if hasattr(provider, "aclose"):
            await provider.aclose()


def _write_generation_results(results, output: Path, output_dir: Path) -> None:
    if len(results) == 1:
        path = write_bytes(output, results[0].image)
        print(path)
        return
    for index, result in enumerate(results, start=1):
        path = write_bytes(output_dir / f"image-{index}.png", result.image)
        print(path)


def _require_gpt_provider(provider: ImageProvider, scenario: str) -> None:
    if not isinstance(provider, GPTImageProvider):
        raise ValueError(f"{scenario} requires --model gpt-image-2")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
