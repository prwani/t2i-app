#!/usr/bin/env python3
"""CLI for end-to-end image asset workflows."""

import argparse
import asyncio
import json
from pathlib import Path

from t2i_core import EvaluationPipeline, GPTImageProvider, Settings
from t2i_core.scenarios import adapt_aspect_ratios, generate_ranked_variations
from t2i_core.utils import write_bytes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create image design assets with t2i_core.")
    parser.add_argument("--workflow", required=True, choices=["best-of-n", "multi-platform"])
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--formats", default="instagram_square,linkedin_banner")
    parser.add_argument("--layers", default="embedding,rubric,judge")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--output-dir", default="outputs")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = Settings()
    provider = GPTImageProvider(settings)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        if args.workflow == "best-of-n":
            pipeline = EvaluationPipeline(settings)
            try:
                ranked = await generate_ranked_variations(
                    provider,
                    args.prompt,
                    n=args.n,
                    quality=args.quality,
                    pipeline=pipeline,
                    layers=[layer.strip() for layer in args.layers.split(",") if layer.strip()],  # type: ignore[arg-type]
                )
            finally:
                await pipeline.embedding.http_client.aclose()
            report = []
            for item in ranked:
                path = write_bytes(output_dir / f"rank-{item.rank}.png", item.generation.image)
                report.append({
                    "rank": item.rank,
                    "path": str(path),
                    "composite_score": item.evaluation.composite_score if item.evaluation else None,
                    "decision": item.evaluation.threshold_decision if item.evaluation else None,
                })
            report_path = output_dir / "ranking.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(report_path)
        else:
            adapted = await adapt_aspect_ratios(
                provider,
                args.prompt,
                [item.strip() for item in args.formats.split(",") if item.strip()],
                quality=args.quality,
            )
            for item in adapted:
                path = write_bytes(output_dir / f"{item.target_format}.png", item.result.image)
                print(path)
    finally:
        await provider.client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
