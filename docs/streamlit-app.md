# Streamlit app

The Streamlit app lives in `app/` and provides an image-focused user interface.

Run locally:

```bash
streamlit run app/Home.py
```

## Pages

- Home
- Image Generate
- Evaluate
- Compare
- Batch Rank

## Authentication model

The app does not implement user management in Python. For production deployment, protect the entire app with Microsoft Entra ID at Azure Container Apps ingress.

## Storage model

Generated images are kept in Streamlit session state and offered as downloads. Container Apps replicas are stateless, so durable multi-user storage should be added with Azure Blob Storage in a later phase if needed.

## Health endpoint

Use Streamlit's built-in health endpoint:

```text
/_stcore/health
```
