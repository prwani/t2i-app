# T2I App

T2I App is an Azure Foundry image generation and evaluation project. It provides a Python SDK, agent skills, and a Streamlit UI for generating images with deployed image models, evaluating prompt adherence and quality, comparing outputs, and ranking generated variations.

The current implementation focuses on image workflows. Video generation is intentionally deferred until video model access is available.

## Get started locally

Create a Python 3.11 environment, install the SDK with app dependencies, and copy the environment template:

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e "packages/t2i_core[dev,app]"
cp .env.example .env
```

Update `.env` with your Azure Foundry, Azure OpenAI, Azure AI Vision, and deployment settings. Local authentication uses Azure AD:

```bash
az login
pytest packages/t2i_core/tests
```

Run the Streamlit UI:

```bash
streamlit run app/Home.py
```

## Get started with Azure deployment

The app is container-ready for Azure Container Apps with Microsoft Entra ID authentication at ingress and managed identity for Azure Foundry/API access.

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
- [SDK](docs/sdk.md)
- [Image scenarios](docs/scenarios.md)
- [Evaluation pipeline](docs/evaluation.md)
- [Streamlit app](docs/streamlit-app.md)
- [Generation skill](skills/t2i-generation/SKILL.md)
- [Evaluation skill](skills/t2i-evaluation/SKILL.md)
- [Design assets skill](skills/t2i-design-assets/SKILL.md)
