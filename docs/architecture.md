# Architecture

T2I App is organized around a shared Python SDK, three agent skills, and a Streamlit UI. The SDK is the source of truth for Azure client construction, model providers, image scenarios, evaluation, types, and utilities. Skills and the UI import the SDK instead of duplicating implementation logic.

```text
Users / Agents / Streamlit UI
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
Azure Foundry, Azure OpenAI, Azure AI Vision
```

## Current scope

The current implementation is image-focused:

- Text-to-image generation.
- Image editing and composition where supported by the provider.
- Prompt adherence and visual-quality evaluation.
- Streamlit UI for generation, evaluation, comparison, and ranking.
- Azure Container Apps deployment with Microsoft Entra ID ingress auth.

Video generation is deferred until video model access is available.

## Authentication

Local development uses Azure AD through `DefaultAzureCredential`, usually after `az login`.

Azure Container Apps should use a managed identity. When using a user-assigned identity, set `AZURE_CLIENT_ID` so the SDK uses the intended identity.
