# Developer notebooks

Executable notebooks for common image-generation and evaluation workflows.

## Setup

From the repository root, install the SDK and launch Jupyter:

```bash
uv pip install -e "packages/t2i_core[dev,app]"
python -m pip install notebook ipykernel
jupyter notebook notebooks/
```

Configure Azure auth with environment variables or a local `.env` file. Do not commit secrets.

Required variables include:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_VISION_ENDPOINT`
- `FOUNDRY_PROJECT_ENDPOINT` when your MAI service endpoint cannot be inferred from Azure OpenAI
- `MAI_IMAGE_2E_DEPLOYMENT` for the default efficient MAI model
- `MAI_IMAGE_2_5_FLASH_DEPLOYMENT` and `MAI_IMAGE_2_5_DEPLOYMENT` for the MAI 2.5 models
- `GPT_IMAGE_2_DEPLOYMENT` for GPT image generation, edits, and multi-image composition
- `EVAL_DECOMPOSER_DEPLOYMENT`, `EVAL_RUBRIC_DEPLOYMENT`, `EVAL_JUDGE_DEPLOYMENT` for evaluation/prompt improvement

The notebooks use `DefaultAzureCredential`, so sign in with `az login` or provide managed identity/service principal environment variables.

To avoid accidental spend, network calls are guarded by `RUN_*` environment variables inside each notebook.
