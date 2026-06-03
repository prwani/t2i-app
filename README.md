# T2I App

T2I App is an Azure Foundry image generation and evaluation project. It provides a Python SDK, a FastAPI backend, a Next.js web experience, agent skills, developer notebooks, and the original Streamlit prototype for generating images, evaluating prompt adherence and quality, comparing outputs, and ranking generated variations.

The current implementation focuses on image workflows. Video generation is intentionally deferred until video model access is available.

Supported image deployments include `gpt-image-2`, `MAI-Image-2`, `MAI-Image-2e`, `MAI-Image-2.5-Flash`, and `MAI-Image-2.5`. Use `MAI-Image-2e` as the default for most generation-only scenarios, and switch to `gpt-image-2` for image-edit/source-image workflows.

## Get started locally

Create a Python 3.11 environment, install the SDK with API and app dependencies, and copy the environment template:

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e "packages/t2i_core[dev,app,api]"
cp .env.example .env
```

Update `.env` with your Azure Foundry, Azure OpenAI, Azure AI Vision, and deployment settings, including the MAI 2.5 deployment variables from `.env.example` when available. Local authentication uses Azure AD:

```bash
az login
pytest packages/t2i_core/tests
```

### Preferred web + API experience

Run the FastAPI backend from the repository root:

```bash
uvicorn api.main:app --reload --port 8000
```

In a second terminal, run the Next.js frontend:

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend reads `NEXT_PUBLIC_API_BASE_URL` and defaults to `http://localhost:8000`.

### Streamlit prototype

The Streamlit UI is retained as a prototype/legacy experience:

```bash
streamlit run app/Home.py
```

### Developer workflows

- [Developer notebooks](notebooks/README.md) provide executable generation, prompt-improvement, and evaluation workflows.
- [TechCommunity-style blog](blog/techcommunity-image-asset-workflow.html) describes the image asset workflow for publication or sharing.

## Get started with Azure deployment

The existing Streamlit app is container-ready for Azure Container Apps with Microsoft Entra ID authentication at ingress and managed identity for Azure Foundry/API access.

Build and deploy using the guidance in [Azure Container Apps deployment](docs/azure-container-apps.md). At a high level:

```bash
az acr build --registry <acr-name> --image t2i-app:latest .
az containerapp create --name t2i-app --image <acr-name>.azurecr.io/t2i-app:latest --target-port 8000 --ingress external
```

After deployment, enable Microsoft Entra authentication on the Container App and grant the managed identity the required Cognitive Services/Foundry roles.

## Detailed documentation

- [Azure Container Apps deployment](docs/azure-container-apps.md)
- [Documentation index](docs/index.md)
- [Architecture](docs/architecture.md)
- [Web and API app](docs/web-app.md)
- [SDK](docs/sdk.md)
- [Image scenarios](docs/scenarios.md)
- [Evaluation pipeline](docs/evaluation.md)
- [Streamlit app](docs/streamlit-app.md)
- [Developer notebooks](notebooks/README.md)
- [Generation skill](skills/t2i-generation/SKILL.md)
- [Evaluation skill](skills/t2i-evaluation/SKILL.md)
- [Design assets skill](skills/t2i-design-assets/SKILL.md)
