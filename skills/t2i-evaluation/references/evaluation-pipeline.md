# Evaluation pipeline reference

The pipeline runs only the selected layers and normalizes the composite score across active layers.

## Default layers

- `embedding`: Azure AI Vision text/image vectors
- `rubric`: prompt decomposition plus image question answering
- `judge`: visual quality scoring

## Thresholds

Defaults live in `t2i_core.settings.EvaluationThresholds`. Tune these for each workflow. In live smoke tests, Azure Vision embedding scores for good image-prompt matches landed below `0.50`, so use local calibration rather than treating defaults as universal.

## Cost and latency

Full evaluation calls Azure Vision plus two or more Azure OpenAI requests. For batch ranking, cap the number of images and show progress to users.
