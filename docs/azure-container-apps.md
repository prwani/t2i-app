# Azure Container Apps deployment

The FastAPI backend is designed to run behind Azure Container Apps ingress with Microsoft Entra ID authentication enabled at the platform layer. The Next.js frontend can run separately and call this API through `NEXT_PUBLIC_API_BASE_URL`.

## Prerequisites

- A Microsoft Foundry resource and project already exist.
- The model deployments used by the app already exist in that project.
- Local `.env` is updated with the Foundry project endpoint, Azure OpenAI endpoint, Azure AI Vision endpoint, and deployment names from `.env.example`.
- Azure CLI is logged in with access to create or update the resource group, ACR, managed identity, Log Analytics workspace, and Container App.

## Configure deployment variables

```bash
RG=<resource-group>
LOCATION=<azure-region>
ACR=<globally-unique-acr-name>
APP=t2i-app
ENV=t2i-env
LAW=t2i-law
MI=t2i-app-mi
```

## Create supporting Azure resources

```bash
az acr create \
  --name "$ACR" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --sku Basic

az identity create \
  --name "$MI" \
  --resource-group "$RG" \
  --location "$LOCATION"

az monitor log-analytics workspace create \
  --resource-group "$RG" \
  --workspace-name "$LAW" \
  --location "$LOCATION"

LAW_ID=$(az monitor log-analytics workspace show \
  --resource-group "$RG" \
  --workspace-name "$LAW" \
  --query customerId -o tsv)

LAW_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group "$RG" \
  --workspace-name "$LAW" \
  --query primarySharedKey -o tsv)

az containerapp env create \
  --name "$ENV" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --logs-workspace-id "$LAW_ID" \
  --logs-workspace-key "$LAW_KEY"
```

Creating the Log Analytics workspace explicitly avoids ambiguous waits during automatic workspace creation.

## Grant managed identity access

Grant the Container Apps managed identity access to pull from ACR and call the configured model resources.

```bash
MI_PRINCIPAL=$(az identity show \
  --name "$MI" \
  --resource-group "$RG" \
  --query principalId -o tsv)

ACR_ID=$(az acr show \
  --name "$ACR" \
  --resource-group "$RG" \
  --query id -o tsv)

AI_ACCOUNT_ID=<cognitive-services-or-ai-services-account-resource-id>
FOUNDRY_PROJECT_ID=<microsoft-foundry-project-resource-id>

az role assignment create \
  --assignee-object-id "$MI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role AcrPull \
  --scope "$ACR_ID"

az role assignment create \
  --assignee-object-id "$MI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" \
  --scope "$AI_ACCOUNT_ID"

az role assignment create \
  --assignee-object-id "$MI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services User" \
  --scope "$AI_ACCOUNT_ID"

az role assignment create \
  --assignee-object-id "$MI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" \
  --scope "$FOUNDRY_PROJECT_ID"

az role assignment create \
  --assignee-object-id "$MI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services User" \
  --scope "$FOUNDRY_PROJECT_ID"
```

Some tenants only require account-scope RBAC; project-scope assignments are included because Microsoft Foundry projects can require project-level access for model invocation.

## Build and push

Use a unique image tag for each deployment so Container Apps creates a new revision instead of reusing a cached `latest` tag.

```bash
TAG=deploy-$(date +%Y%m%d%H%M%S)

az acr build \
  --registry "$ACR" \
  --image "t2i-app:$TAG" \
  .
```

## Create environment variables from `.env`

The app reads runtime configuration from environment variables. Reuse the local `.env` file, add `AZURE_CLIENT_ID` for the user-assigned identity, and do not print or commit secrets.

```bash
MI_ID=$(az identity show \
  --name "$MI" \
  --resource-group "$RG" \
  --query id -o tsv)

MI_CLIENT_ID=$(az identity show \
  --name "$MI" \
  --resource-group "$RG" \
  --query clientId -o tsv)

python - <<'PY' > /tmp/t2i-env-vars.txt
from pathlib import Path

keys = [
    "FOUNDRY_PROJECT_ENDPOINT",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_VISION_ENDPOINT",
    "MAI_IMAGE_2_DEPLOYMENT",
    "MAI_IMAGE_2E_DEPLOYMENT",
    "MAI_IMAGE_2_5_FLASH_DEPLOYMENT",
    "MAI_IMAGE_2_5_DEPLOYMENT",
    "GPT_IMAGE_2_DEPLOYMENT",
    "EVAL_DECOMPOSER_DEPLOYMENT",
    "EVAL_RUBRIC_DEPLOYMENT",
    "EVAL_JUDGE_DEPLOYMENT",
    "AZURE_OPENAI_SCOPE",
    "AZURE_VISION_SCOPE",
]

values = {}
for line in Path(".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    values[key.strip()] = value.strip().strip('"').strip("'")

values["AZURE_CLIENT_ID"] = "__AZURE_CLIENT_ID__"
for key in [*keys, "AZURE_CLIENT_ID"]:
    value = values.get(key)
    if value:
        print(f"{key}={value}")
PY

sed -i "s#__AZURE_CLIENT_ID__#$MI_CLIENT_ID#" /tmp/t2i-env-vars.txt
```

## Create or update the container app

```bash
IMAGE="$ACR.azurecr.io/t2i-app:$TAG"

az containerapp create \
  --name "$APP" \
  --resource-group "$RG" \
  --environment "$ENV" \
  --image "$IMAGE" \
  --target-port 8000 \
  --ingress external \
  --registry-server "$ACR.azurecr.io" \
  --registry-identity "$MI_ID" \
  --user-assigned "$MI_ID" \
  --env-vars $(cat /tmp/t2i-env-vars.txt)
```

For an existing app, update the image and environment variables:

```bash
az containerapp update \
  --name "$APP" \
  --resource-group "$RG" \
  --image "$IMAGE" \
  --revision-suffix "${TAG//deploy-/d}" \
  --set-env-vars $(cat /tmp/t2i-env-vars.txt)
```

Enable Microsoft Entra authentication on the Container App after creation. Restrict access to the tenant, application, group, or app role appropriate for your deployment.

## Smoke test

```bash
FQDN=$(az containerapp show \
  --name "$APP" \
  --resource-group "$RG" \
  --query properties.configuration.ingress.fqdn -o tsv)

curl -fsS "https://$FQDN/health"
curl -fsS "https://$FQDN/api/scenarios"
```

To verify managed identity access to the configured models, run one generation request:

```bash
curl -fsS --max-time 360 \
  -X POST "https://$FQDN/api/generations" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "text-to-image",
    "model": "MAI-Image-2e",
    "prompt": "A simple blue circle icon on a white background, minimal vector style, no text",
    "size": "1024x1024",
    "quality": "low",
    "n": 1
  }'
```

## Storage note

The API stores generated images on local writable container storage (`/tmp/t2i-generated-assets` by default) for download. Container Apps replicas are stateless, so use Azure Blob Storage in a later phase if assets need durable multi-user storage.
