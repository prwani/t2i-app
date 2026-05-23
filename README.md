# T2I App

Local monorepo for text-to-image generation and image evaluation on Azure Foundry.

Video generation is intentionally deferred until Sora 2 access is available. The current SDK focuses on image providers, image-only scenarios, and the image evaluation pipeline.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e "packages/t2i_core[dev]"
az login
cp .env.example .env
pytest packages/t2i_core/tests
```

Authentication uses Azure AD through `DefaultAzureCredential`; API keys are not required by default.

## Image SDK quick start

```python
from t2i_core import GPTImageProvider, Settings

settings = Settings()
provider = GPTImageProvider(settings)
images = await provider.generate("A clean product hero image on a blue background")
```

Available image providers:

- `MAIImageProvider`: MAI-Image-2 / MAI-Image-2e text-to-image generation through the Foundry `/mai/v1/images/generations` API.
- `GPTImageProvider`: GPT-Image-2 text-to-image generation plus editing, inpainting, and image composition.

Available image scenarios are in `t2i_core.scenarios`: brand templates, multi-image composition, multi-turn refinement, inpainting, product placement, batch variations, text rendering, and aspect-ratio adaptation.

Image evaluation supports standalone `EmbeddingEvaluator`, `RubricEvaluator`, and `LLMJudgeEvaluator`, plus `EvaluationPipeline` for selective or full-layer scoring.
