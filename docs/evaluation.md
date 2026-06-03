# Evaluation pipeline

The evaluation module provides standalone evaluators plus a full pipeline.

## Layers

| Layer | Class | Purpose |
| --- | --- | --- |
| Embedding | `EmbeddingEvaluator` | Broad semantic alignment between prompt and image using Azure AI Vision vectors |
| Rubric | `RubricEvaluator` | Prompt decomposition and per-attribute verification |
| Judge | `LLMJudgeEvaluator` | Visual quality, coherence, style, aesthetics, and text legibility when relevant |
| Pipeline | `EvaluationPipeline` | Runs selected layers and computes a normalized composite score |

## Selective execution

Run only the layers needed for the workflow:

```python
report = await EvaluationPipeline(settings).evaluate(
    image,
    prompt,
    layers=["embedding", "rubric"],
)
```

Skipped layers are not called and do not contribute zeroes to the composite score. Active weights are renormalized.

## Thresholds

Defaults live in `EvaluationThresholds` and should be calibrated for your image types. Azure Vision embedding cosine values are not percentages; good matches may still score below `0.50` depending on prompt and image.

## UI behavior

The web app exposes layer selection through the FastAPI backend. Full evaluation uses Azure Vision plus Azure OpenAI calls, so it has higher latency and cost than embedding-only checks.
