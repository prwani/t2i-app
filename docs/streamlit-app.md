# Streamlit prototype

The Streamlit app lives in `app/` and provides the original image-focused prototype/legacy user interface. For new UI work, prefer the Next.js + FastAPI app described in [Web and API app](web-app.md).

Run locally:

```bash
streamlit run app/Home.py
```

## Navigation

- Create
  - Asset Creation Workflow: text-to-image generation, brand template, text rendering, aspect-ratio package, multi-image composition, inpainting, product placement, and multi-turn refinement
- Evaluation Utils
  - Evaluate
  - Compare
  - Batch Rank

Asset Creation Workflow is the app homepage. It defaults to `MAI-Image-2e` for generation-only scenarios. Scenarios that require image editing or source-image inputs automatically use `gpt-image-2`.

The Asset Creation Workflow page provides per-scenario example prompts. Scenarios with additional inputs also prefill useful defaults, such as brand colors, multi-line rendered text, aspect-ratio formats, product placement environments, and refinement instructions. Multi-image composition, inpainting, and product placement examples include GPT-generated local sample input images that users can try before uploading their own references.

The prompt box includes an "Improve with AI" action that uses the configured Azure OpenAI text model to rewrite the current prompt with clearer scene structure, subject details, composition, lighting, constraints, and scenario-specific guidance.

After generation, Asset Creation Workflow includes an "Evaluate generated results" step. It uses scenario-aware default layers, shows the same score-summary matrix used by Compare/Evaluate, highlights the best candidate by composite score, and keeps detailed reports below the generated-image gallery. A compact top stepper shows Generate as active first, then marks it complete and activates Evaluate / Compare after assets are generated. Standalone Evaluate and Compare pages remain available under Evaluation Utils for external uploaded images.

Generated-image galleries use an in-page large preview with Previous/Next controls, thumbnails, and a selected-image download button. This avoids relying on Streamlit's built-in image maximize overlay for multi-image navigation.

## Authentication model

The app does not implement user management in Python. For production deployment, protect the entire app with Microsoft Entra ID at Azure Container Apps ingress.

## Storage model

Generated images are kept in Streamlit session state and offered as downloads. Container Apps replicas are stateless, so durable multi-user storage should be added with Azure Blob Storage in a later phase if needed.

## Health endpoint

Use Streamlit's built-in health endpoint:

```text
/_stcore/health
```
