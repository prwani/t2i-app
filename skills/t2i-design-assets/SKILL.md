---
name: t2i-design-assets
description: |
  Create production-oriented image assets by chaining generation, evaluation, adaptation, and ranking.
  USE FOR: create design assets, generate and pick the best, brand images for UI,
  social media image package, hero images, quality-gated visual assets.
  DO NOT USE FOR: video generation, evaluation-only work, or UI code review.
---

# T2I Design Assets

Use this skill for end-to-end image asset workflows. It chains the generation and evaluation SDK surfaces without duplicating implementation logic.

## CLI

```bash
python skills/t2i-design-assets/scripts/create_assets.py --workflow best-of-n --prompt "A product hero image" --n 3 --output-dir outputs
python skills/t2i-design-assets/scripts/create_assets.py --workflow multi-platform --prompt "A launch banner" --formats instagram_square,linkedin_banner --output-dir outputs
```

## Workflows

- `best-of-n`: generate N variations, evaluate each, and rank by composite score.
- `multi-platform`: generate the same concept for supported target formats.

Video workflows are deferred until video model access is available.
