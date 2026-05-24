# Streamlit app

The Streamlit app lives in `app/` and provides an image-focused user interface.

Run locally:

```bash
streamlit run app/Home.py
```

## Pages

- Home
- Image Generate: text generation, brand template, text rendering, aspect-ratio package, multi-image composition, inpainting, product placement, and multi-turn refinement
- Evaluate
- Compare
- Batch Rank

The Image Generate page provides per-scenario example prompts. Scenarios with additional inputs also prefill useful defaults, such as brand colors, exact text, aspect-ratio formats, product placement environments, and refinement instructions.

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
