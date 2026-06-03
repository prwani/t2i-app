# Azure Container Apps deployment

The complete solution runs as two Azure Container Apps in the same Container Apps environment:

- `t2i-app`: FastAPI backend on port 8000.
- `t2i-web`: Next.js frontend on port 3000, built with `NEXT_PUBLIC_API_BASE_URL` pointing to the backend URL.

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
API_APP=t2i-app
WEB_APP=t2i-web
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
API_TAG=api-$(date +%Y%m%d%H%M%S)

az acr build \
  --registry "$ACR" \
  --image "t2i-app:$API_TAG" \
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
API_IMAGE="$ACR.azurecr.io/t2i-app:$API_TAG"

az containerapp create \
  --name "$API_APP" \
  --resource-group "$RG" \
  --environment "$ENV" \
  --image "$API_IMAGE" \
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
  --name "$API_APP" \
  --resource-group "$RG" \
  --image "$API_IMAGE" \
  --revision-suffix "${API_TAG//api-/a}" \
  --set-env-vars $(cat /tmp/t2i-env-vars.txt)
```

## Smoke test the backend

```bash
API_FQDN=$(az containerapp show \
  --name "$API_APP" \
  --resource-group "$RG" \
  --query properties.configuration.ingress.fqdn -o tsv)

API_BASE_URL="https://$API_FQDN"

curl -fsS "$API_BASE_URL/health"
curl -fsS "$API_BASE_URL/api/scenarios"
```

To verify managed identity access to the configured models, run one generation request:

```bash
curl -fsS --max-time 360 \
  -X POST "$API_BASE_URL/api/generations" \
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

## Build and deploy the frontend

Build the Next.js frontend with the deployed backend URL. `NEXT_PUBLIC_API_BASE_URL` is a build-time setting for the browser bundle, so use a unique frontend image tag whenever the backend URL changes.

```bash
WEB_TAG=web-$(date +%Y%m%d%H%M%S)

az acr build \
  --registry "$ACR" \
  --file web/Dockerfile \
  --build-arg NEXT_PUBLIC_API_BASE_URL="$API_BASE_URL" \
  --image "t2i-web:$WEB_TAG" \
  .
```

Create the frontend Container App:

```bash
WEB_IMAGE="$ACR.azurecr.io/t2i-web:$WEB_TAG"

az containerapp create \
  --name "$WEB_APP" \
  --resource-group "$RG" \
  --environment "$ENV" \
  --image "$WEB_IMAGE" \
  --target-port 3000 \
  --ingress external \
  --registry-server "$ACR.azurecr.io" \
  --registry-identity "$MI_ID" \
  --user-assigned "$MI_ID"
```

For an existing frontend app, update the image:

```bash
az containerapp update \
  --name "$WEB_APP" \
  --resource-group "$RG" \
  --image "$WEB_IMAGE" \
  --revision-suffix "${WEB_TAG//web-/w}"
```

Allow the deployed frontend origin through backend CORS:

```bash
WEB_FQDN=$(az containerapp show \
  --name "$WEB_APP" \
  --resource-group "$RG" \
  --query properties.configuration.ingress.fqdn -o tsv)

WEB_ORIGIN="https://$WEB_FQDN"

az containerapp update \
  --name "$API_APP" \
  --resource-group "$RG" \
  --set-env-vars CORS_ALLOWED_ORIGINS="$WEB_ORIGIN"
```

Enable Microsoft Entra authentication on both Container Apps after creation. Restrict access to the tenant, application, group, or app role appropriate for your deployment. If ingress auth is enabled on both apps, ensure the frontend can still call the backend API according to your chosen auth policy.

## Smoke test the frontend and CORS

```bash
curl -fsS "$WEB_ORIGIN/health"
curl -fsS "$WEB_ORIGIN/" | grep -i "Asset Creation Workflow"

curl -fsS -I \
  -X OPTIONS "$API_BASE_URL/api/scenarios" \
  -H "Origin: $WEB_ORIGIN" \
  -H "Access-Control-Request-Method: GET" \
  | grep -i "access-control-allow-origin"

curl -fsS "$WEB_ORIGIN/" | grep "$API_BASE_URL"
```

The last check verifies that the frontend bundle was built with the deployed backend URL.

## Storage note

The API stores generated images on local writable container storage (`/tmp/t2i-generated-assets` by default) for download. Container Apps replicas are stateless, so use Azure Blob Storage in a later phase if assets need durable multi-user storage.
