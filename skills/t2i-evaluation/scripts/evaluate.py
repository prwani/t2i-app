#!/usr/bin/env python3
"""CLI for image evaluation."""

import argparse
import asyncio
import json
from pathlib import Path

from t2i_core import EvaluationPipeline, Settings
from t2i_core.evaluation.pipeline import EvaluationLayer
from t2i_core.utils import read_image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate images with t2i_core.")
    parser.add_argument("--image", help="Single image path.")
    parser.add_argument("--images-dir", help="Directory of .png/.jpg/.jpeg/.webp images.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--layers", default="embedding,rubric,judge")
    parser.add_argument("--output", default="evaluation-report.json")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    image_paths = _resolve_image_paths(args)
    layers = [layer.strip() for layer in args.layers.split(",") if layer.strip()]
    settings = Settings()
    pipeline = EvaluationPipeline(settings)
    reports = []
    try:
        for image_path in image_paths:
            report = await pipeline.evaluate(
                read_image(image_path),
                args.prompt,
                layers=layers,  # type: ignore[arg-type]
                image_path=str(image_path),
            )
            reports.append(report.model_dump(mode="json"))
    finally:
        await pipeline.embedding.http_client.aclose()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports[0] if len(reports) == 1 else reports, indent=2), encoding="utf-8")
    print(output)


def _resolve_image_paths(args: argparse.Namespace) -> list[Path]:
    if args.image:
        return [Path(args.image)]
    if args.images_dir:
        directory = Path(args.images_dir)
        paths = sorted(
            path for path in directory.iterdir()
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )
        if paths:
            return paths
    raise ValueError("Provide --image or --images-dir with at least one image")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
