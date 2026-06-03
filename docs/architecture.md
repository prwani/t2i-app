# Architecture

T2I App is organized around a shared Python SDK, a FastAPI backend, a Next.js frontend, three agent skills, and developer notebooks. The SDK is the source of truth for Azure client construction, model providers, image scenarios, evaluation, types, and utilities. The API, web UI, skills, and notebooks import the SDK instead of duplicating implementation logic.

```text
Users
  |
  +-- Next.js web UI (web/) --> FastAPI backend (api/)
  |
  +-- Agent skills (skills/) and notebooks (notebooks/)
                                 |
                                 v
                              t2i_core
                                 |
                                 +-- providers: GPT image and MAI image
                                 +-- scenarios: reusable image workflows
                                 +-- evaluation: embedding, rubric, judge, pipeline
                                 +-- settings, types, utilities
                                 |
                                 v
Microsoft Foundry, Azure OpenAI, Azure AI Vision
```

## Current scope

The current implementation is image-focused:

- Text-to-image generation.
- Image editing and composition where supported by the provider.
- Prompt adherence and visual-quality evaluation.
- Preferred Next.js + FastAPI UI for asset creation workflows.
- Developer notebooks for generation, prompt improvement, and evaluation/ranking workflows.
- Azure Container Apps deployment with Microsoft Entra ID ingress auth.

Video generation is deferred until video model access is available.

## Authentication

Local development uses Azure AD through `DefaultAzureCredential`, usually after `az login`.

Azure Container Apps should use a managed identity. When using a user-assigned identity, set `AZURE_CLIENT_ID` so the SDK uses the intended identity.

## Application surfaces

- `web/` is the preferred local UI. It calls the backend through `NEXT_PUBLIC_API_BASE_URL`.
- `api/` exposes scenario metadata, prompt improvement, generation, evaluation, and comparison endpoints.
- `app/` contains shared application services and sample assets used by the API.
- `notebooks/` contains executable developer workflows.
