# Azure Container Apps deployment

The Streamlit UI is designed to run behind Azure Container Apps ingress with Microsoft Entra ID authentication enabled at the platform layer.

## Build and push

```bash
az acr build \
  --registry <acr-name> \
  --image t2i-app:latest \
  .
```

## Required environment variables

```bash
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_VISION_ENDPOINT=https://<resource>.cognitiveservices.azure.com/
MAI_IMAGE_2_DEPLOYMENT=MAI-Image-2
MAI_IMAGE_2E_DEPLOYMENT=MAI-Image-2e
MAI_IMAGE_2_5_FLASH_DEPLOYMENT=MAI-Image-2.5-Flash
MAI_IMAGE_2_5_DEPLOYMENT=MAI-Image-2.5
GPT_IMAGE_2_DEPLOYMENT=gpt-image-2
EVAL_DECOMPOSER_DEPLOYMENT=o4-mini
EVAL_RUBRIC_DEPLOYMENT=o4-mini
EVAL_JUDGE_DEPLOYMENT=gpt-5.4
```

For a user-assigned managed identity, set:

```bash
AZURE_CLIENT_ID=<managed-identity-client-id>
```

## RBAC

Grant the Container Apps managed identity:

- `Cognitive Services OpenAI User` on the Azure OpenAI or Azure AI Services resource.
- `Cognitive Services User` on the Azure AI Vision or Azure AI Services resource.
- Project-level access in Azure Foundry if your tenant requires it for model invocation.

## Create or update the container app

```bash
az containerapp create \
  --name t2i-app \
  --resource-group <resource-group> \
  --environment <container-apps-environment> \
  --image <acr-name>.azurecr.io/t2i-app:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server <acr-name>.azurecr.io \
  --user-assigned <managed-identity-resource-id> \
  --env-vars \
    FOUNDRY_PROJECT_ENDPOINT=<foundry-project-endpoint> \
    AZURE_OPENAI_ENDPOINT=<openai-endpoint> \
    AZURE_VISION_ENDPOINT=<vision-endpoint> \
    AZURE_CLIENT_ID=<managed-identity-client-id>
```

Enable Microsoft Entra authentication on the Container App after creation. Restrict access to the tenant, application, group, or app role appropriate for your deployment.

## Health probe

Use Streamlit's health endpoint:

```text
/_stcore/health
```

## Storage note

The app keeps generated images in Streamlit session state for download. Container Apps replicas are stateless, so use Azure Blob Storage in a later phase if assets need durable multi-user storage.
