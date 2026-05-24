# SDK

The SDK lives in `packages/t2i_core` and is installed locally with:

```bash
pip install -e "packages/t2i_core[dev,app]"
```

## Public surfaces

Core imports:

```python
from t2i_core import (
    Settings,
    GPTImageProvider,
    MAIImageProvider,
    EmbeddingEvaluator,
    PromptDecomposer,
    RubricEvaluator,
    LLMJudgeEvaluator,
    EvaluationPipeline,
)
```

## Settings

`Settings` loads endpoints, deployment names, scopes, evaluation thresholds, and evaluation weights from environment variables.

Key variables:

- `FOUNDRY_PROJECT_ENDPOINT`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_VISION_ENDPOINT`
- `GPT_IMAGE_2_DEPLOYMENT`
- `MAI_IMAGE_2_DEPLOYMENT`
- `MAI_IMAGE_2E_DEPLOYMENT`
- `EVAL_DECOMPOSER_DEPLOYMENT`
- `EVAL_RUBRIC_DEPLOYMENT`
- `EVAL_JUDGE_DEPLOYMENT`
- `AZURE_CLIENT_ID` for user-assigned managed identity in Azure Container Apps

## Providers

`GPTImageProvider` supports:

- Text-to-image generation.
- Image editing.
- Inpainting with an optional PNG alpha mask.
- Multi-image composition.

`MAIImageProvider` supports:

- Text-to-image generation through the Foundry MAI image API.

## Utilities

The SDK uses bytes internally for image data. Utility helpers cover base64 encoding/decoding, image reads/writes, prompt trimming, and validation for Azure Vision image constraints.
