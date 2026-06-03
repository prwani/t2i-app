# Image generation reference

The generation skill imports `t2i_core` and does not duplicate SDK logic.

## Environment

Required:

- `FOUNDRY_PROJECT_ENDPOINT`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_VISION_ENDPOINT`
- `GPT_IMAGE_2_DEPLOYMENT`
- `MAI_IMAGE_2_DEPLOYMENT`
- `MAI_IMAGE_2E_DEPLOYMENT`
- `MAI_IMAGE_2_5_FLASH_DEPLOYMENT`
- `MAI_IMAGE_2_5_DEPLOYMENT`

Optional for Azure Container Apps user-assigned managed identity:

- `AZURE_CLIENT_ID`

## Scenario mapping

| Scenario | Provider | Notes |
| --- | --- | --- |
| `text` | GPT or MAI | Text-to-image generation |
| `brand-template` | GPT or MAI | Adds brand constraints to prompt |
| `text-rendering` | GPT preferred | Prompts for exact readable text |
| `aspect-ratio` | GPT or MAI | Uses API-supported sizes |
| `inpainting` | GPT only | Optional PNG alpha mask |
| `composition` | GPT only | Requires 2-16 source images |
| `product-placement` | GPT only | Edits a product image into environments |

## Supported sizes

Use API-supported sizes such as `1024x1024`, `1536x1024`, and `1024x1536`.
