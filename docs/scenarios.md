# Image scenarios

Image scenarios live under `t2i_core.scenarios`. They are thin orchestration helpers over SDK providers and evaluators.

## Available scenarios

| Scenario | Function | Provider |
| --- | --- | --- |
| Text-to-image generation | Provider `generate()` | GPT image or MAI image |
| Brand template | `generate_brand_asset()` | GPT image or MAI image |
| Text rendering | `generate_text_rendering()` | GPT image preferred |
| Aspect ratio adaptation | `adapt_aspect_ratios()` | GPT image or MAI image |
| Multi-image composition | `compose_images()` | GPT image |
| Multi-turn refinement | `refine_image_chain()` | GPT image |
| Inpainting | `inpaint_image()` | GPT image |
| Product placement | `place_product()` | GPT image |
| Batch variations and ranking | `generate_ranked_variations()` | GPT image plus evaluation pipeline |

## Size presets

Use API-supported generation sizes:

- `1024x1024`
- `1536x1024`
- `1024x1536`

Format helpers map common targets such as `instagram_square`, `instagram_story`, `linkedin_banner`, `desktop_hero`, and `mobile_story` to supported API sizes.

## Notes

- Editing workflows require `gpt-image-2`.
- MAI image providers are generation-only.
- Batch ranking can be expensive because it evaluates every generated variation.
