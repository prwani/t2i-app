---
name: t2i-evaluation
description: |
  Evaluate generated or uploaded images with Azure AI Vision and Azure OpenAI models through t2i_core.
  Supports embedding alignment, prompt-rubric checks, LLM judge scoring, and full composite pipeline.
  USE FOR: evaluate image quality, score image, compare image to prompt, rank variations,
  quality gate generated image, check prompt adherence.
  DO NOT USE FOR: image generation or video evaluation.
---

# T2I Evaluation

Use this skill to evaluate images with individual evaluators or the full `EvaluationPipeline`.

## CLI

```bash
python skills/t2i-evaluation/scripts/evaluate.py --image hero.png --prompt "A product hero image" --layers embedding
python skills/t2i-evaluation/scripts/evaluate.py --image hero.png --prompt "A product hero image" --layers embedding,rubric,judge --output report.json
python skills/t2i-evaluation/scripts/evaluate.py --images-dir outputs --prompt "A product hero image" --layers embedding,rubric --output batch.json
```

## Layer guide

- `embedding`: fast broad semantic alignment using Azure AI Vision.
- `rubric`: prompt attribute decomposition and prompt-adherence checks.
- `judge`: visual quality and aesthetic scoring.
- `embedding,rubric,judge`: full quality gate with composite score.

## Interpreting results

The embedding score is not a percentage. Calibrate thresholds against your own prompts and generated assets. Rubric and judge scores are usually better for prompt-specific acceptance decisions.
