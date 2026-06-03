---
name: t2i-generation
description: |
  Generate images using Azure Foundry image models through the local t2i_core SDK.
  Supports image generation, editing, inpainting, composition, text rendering, aspect ratio adaptation,
  brand templates, product placement, and batch variations.
  USE FOR: generate image, create hero image, product photo, brand asset, marketing visual,
  inpaint image, edit image, compose images, create social media image assets.
  DO NOT USE FOR: video generation or image quality evaluation.
---

# T2I Generation

Use this skill to generate and edit images with the local `t2i_core` SDK. Video generation is deferred until Sora access is available.

## Setup

From the repository root:

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e "packages/t2i_core[app]"
az login
cp .env.example .env
```

Configure `.env` with Azure Foundry endpoints and deployment names. Authentication uses Azure AD through `DefaultAzureCredential`; API keys are not required by default.

## Model guide

- `gpt-image-2`: image generation plus editing, inpainting, and multi-image composition.
- `mai-image-2`: Foundry MAI image generation.
- `mai-image-2e`: efficient Foundry MAI image generation.

## CLI

```bash
python skills/t2i-generation/scripts/generate.py --scenario text --prompt "A dog at Gateway of India" --model gpt-image-2 --output outputs/dog.png
python skills/t2i-generation/scripts/generate.py --scenario brand-template --prompt "launch banner" --brand-config brand.json --output outputs/brand.png
python skills/t2i-generation/scripts/generate.py --scenario inpainting --image source.png --prompt "make the cube green" --output outputs/edit.png
python skills/t2i-generation/scripts/generate.py --scenario composition --image product.png --image background.png --prompt "place the product in the scene" --output outputs/composed.png
python skills/t2i-generation/scripts/generate.py --scenario aspect-ratio --prompt "product hero" --formats instagram_square,linkedin_banner --output-dir outputs/
```

## Programmatic quick start

```python
from t2i_core import GPTImageProvider, Settings

settings = Settings()
provider = GPTImageProvider(settings)
images = await provider.generate("A clean product hero image on a blue background")
```

## Notes

- Keep generated images out of git.
- Use `quality=low` for smoke tests.
- Use `gpt-image-2`, `MAI-Image-2.5-Flash`, or `MAI-Image-2.5` for single-image edit workflows. Use `gpt-image-2` for multi-image composition.
- Use MAI providers for text-to-image generation only.
