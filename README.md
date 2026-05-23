# T2I App

Local monorepo for text-to-image/video generation and image evaluation on Azure Foundry.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e "packages/t2i_core[dev]"
az login
cp .env.example .env
pytest packages/t2i_core/tests
```

Authentication uses Azure AD through `DefaultAzureCredential`; API keys are not required by default.
