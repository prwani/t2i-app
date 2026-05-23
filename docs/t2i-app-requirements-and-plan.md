# T2I Generation & Evaluation — Requirements + Implementation Plan

> **Purpose**: Self-contained prompt for any coding agent (Claude Code, GitHub Copilot CLI, Cursor, etc.) to build an image/video generation and evaluation system on Microsoft Azure Foundry. Produces a **single local SDK** (`t2i_core`) + **three reusable skills** in [microsoft/skills](https://github.com/microsoft/skills) standard format + a **Streamlit demo app**.

---

## 1. Project Overview

### What We're Building

| Layer | What | Purpose |
|-------|------|---------|
| **SDK** | `t2i_core` Python package | Single shared library — providers, generation scenarios, evaluation (individual techniques + full pipeline), types, utilities. Zero duplication. |
| **Skills** | 3 skills in microsoft/skills format | Agent-consumable knowledge layer. Each skill has a `SKILL.md` + `references/` + `scripts/` that import from `t2i_core`. Any coding agent can discover and use them. |
| **App** | Streamlit web UI | Demo app that consumes the SDK directly. Shows all generation scenarios, evaluation, comparison, and ranking. |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Coding Agents                         │
│         (Claude Code, GitHub Copilot, Cursor)           │
└──────────┬──────────────┬──────────────┬────────────────┘
           │              │              │
    ┌──────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
    │ t2i-        │ │ t2i-     │ │ t2i-design- │   Skills
    │ generation  │ │evaluation│ │ assets      │   (SKILL.md)
    └──────┬──────┘ └────┬─────┘ └──────┬──────┘
           │              │              │
           └──────────────┼──────────────┘
                          │
                   ┌──────▼──────┐
                   │  t2i_core   │   SDK (local editable package)
                   │  (Python)   │
                   └──────┬──────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
  ┌─────▼─────┐   ┌──────▼──────┐   ┌─────▼─────┐
  │ Providers  │   │ Evaluation  │   │  Shared   │
  │ MAI-Image  │   │ Embedding   │   │  Types    │
  │ GPT-Image  │   │ Rubric      │   │  Utils    │
  │ Sora 2     │   │ LLM Judge   │   │  Config   │
  └─────┬──────┘   │ Pipeline    │   └───────────┘
        │          └──────┬──────┘
        │                 │
  ┌─────▼─────────────────▼─────┐
  │      Azure Foundry APIs      │
  │  OpenAI · AI Vision · Sora   │
  └──────────────────────────────┘
```

### Tech Stack

- **Language**: Python 3.11+
- **SDK**: Single package `t2i_core` (replaces previous two-package design)
- **Skills**: 3 skills following [microsoft/skills standard format](https://github.com/microsoft/skills/blob/main/.github/skills/skill-creator/SKILL.md)
- **Web UI**: Streamlit
- **Infrastructure**: Microsoft Azure Foundry (models), Azure AI Vision (embeddings)
- **Package management**: `pyproject.toml` with `uv` or `pip`
- **Testing**: `pytest` with async support

---

## 2. Repository Structure

```
t2i-app/
├── pyproject.toml                      # Monorepo root
├── .env.example
├── README.md
│
├── packages/
│   └── t2i_core/                       # ═══ THE SDK ═══
│       ├── pyproject.toml              # pip install -e packages/t2i_core
│       ├── src/
│       │   └── t2i_core/
│       │       ├── __init__.py
│       │       │
│       │       ├── providers/          # Layer 1: Model providers
│       │       │   ├── __init__.py
│       │       │   ├── base.py         # Abstract ImageProvider / VideoProvider
│       │       │   ├── mai_image.py    # MAI-Image-2 / MAI-Image-2e
│       │       │   ├── gpt_image.py    # GPT-Image-2 (generation + editing)
│       │       │   └── sora_video.py   # Sora 2 (text-to-video, image-to-video)
│       │       │
│       │       ├── scenarios/          # Generation scenarios (use providers)
│       │       │   ├── __init__.py
│       │       │   ├── brand_template.py
│       │       │   ├── multi_image_composition.py
│       │       │   ├── multi_turn_refinement.py
│       │       │   ├── inpainting.py
│       │       │   ├── product_placement.py
│       │       │   ├── batch_variations.py
│       │       │   ├── text_rendering.py
│       │       │   ├── aspect_ratio_adaptation.py
│       │       │   ├── text_to_video.py
│       │       │   └── image_to_video.py
│       │       │
│       │       ├── evaluation/         # ═══ EVALUATION MODULE ═══
│       │       │   ├── __init__.py     # Exports individual evaluators + pipeline
│       │       │   ├── embedding.py    # EmbeddingEvaluator (Layer 1 — standalone)
│       │       │   ├── rubric.py       # RubricEvaluator (Layer 2 — standalone)
│       │       │   ├── judge.py        # LLMJudgeEvaluator (Layer 3 — standalone)
│       │       │   ├── decomposer.py   # PromptDecomposer (shared by L2 + L3)
│       │       │   ├── pipeline.py     # EvaluationPipeline (orchestrates all 3)
│       │       │   └── config.py       # EvalModelConfig + presets
│       │       │
│       │       ├── types.py            # ALL Pydantic models (single source of truth)
│       │       └── utils.py            # Image I/O, base64, auth helpers, cost tracking
│       │
│       └── tests/
│           ├── test_providers.py
│           ├── test_scenarios.py
│           ├── test_evaluation.py
│           └── test_pipeline.py
│
├── skills/                             # ═══ AGENT SKILLS ═══
│   ├── t2i-generation/                 # Skill 1: Image & video generation
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── mai-image-api.md
│   │   │   ├── gpt-image-api.md
│   │   │   ├── sora-video-api.md
│   │   │   └── scenarios.md
│   │   └── scripts/
│   │       └── generate.py             # CLI: python generate.py --scenario brand_template ...
│   │
│   ├── t2i-evaluation/                 # Skill 2: Image quality evaluation
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── embedding-layer.md
│   │   │   ├── rubric-layer.md
│   │   │   ├── judge-layer.md
│   │   │   ├── composite-scoring.md
│   │   │   └── eval-presets.md
│   │   └── scripts/
│   │       └── evaluate.py             # CLI: python evaluate.py --layer embedding|rubric|judge|pipeline ...
│   │
│   └── t2i-design-assets/              # Skill 3: End-to-end asset creation
│       ├── SKILL.md
│       ├── references/
│       │   └── workflows.md
│       └── scripts/
│           └── create_assets.py        # CLI: chains generation → evaluation → adaptation
│
├── app/                                # ═══ STREAMLIT DEMO APP ═══
│   ├── app.py
│   ├── pages/
│   │   ├── 01_generate.py
│   │   ├── 02_video_generate.py
│   │   ├── 03_evaluate.py
│   │   ├── 04_compare.py
│   │   └── 05_batch_rank.py
│   └── components/
│       ├── image_gallery.py
│       ├── score_card.py
│       └── evaluation_report.py
│
├── samples/
│   ├── brand_templates/
│   ├── reference_images/
│   └── sample_prompts.json
│
└── docs/
    └── api_reference.md
```

---

## 3. Environment Variables

```bash
# Azure OpenAI / Foundry — used with Azure AD via DefaultAzureCredential
# Example: https://<your-resource>.openai.azure.com
# The SDK appends /openai/v1/ for v1 API calls.
AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"

# Deployment names — placeholders until real deployments are available.
# These are NOT model URLs; they are the deployment names configured in Azure Foundry.
MAI_IMAGE_2_DEPLOYMENT="mai-image-2"
MAI_IMAGE_2E_DEPLOYMENT="mai-image-2-efficient"
GPT_IMAGE_2_DEPLOYMENT="gpt-image-2"

# Video model deployment
SORA_2_DEPLOYMENT="sora-2"

# Evaluation models — configurable per layer (see EvalModelConfig presets in Section 5.5)
EVAL_RUBRIC_DEPLOYMENT="o4-mini"
EVAL_JUDGE_DEPLOYMENT="gpt-5.4"
EVAL_DECOMPOSER_DEPLOYMENT="o4-mini"

# Optional: single-model override — uses one model for ALL evaluation layers
# EVAL_UNIFIED_DEPLOYMENT="gpt-5.5"

# Azure AI Vision — for multimodal embeddings (Layer 1 evaluation)
AZURE_VISION_ENDPOINT="https://<your-vision-resource>.cognitiveservices.azure.com/"

# Local development auth:
#   az login
#   az account set --subscription "<subscription-id-or-name>"
# Optional when your developer account needs an explicit tenant:
#   AZURE_TENANT_ID="<tenant-id>"
```

### 3.1 Authentication Requirement

Use **Azure AD / Microsoft Entra ID with `DefaultAzureCredential`** as the primary and required authentication path. Do not require API keys in `.env`.

Required Azure RBAC:
- Azure OpenAI / Foundry resource: `Cognitive Services OpenAI User`
- Azure AI Vision resource: `Cognitive Services User`

Python client pattern:
```python
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncOpenAI

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://ai.azure.com/.default",
)

client = AsyncOpenAI(
    base_url=f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1/",
    api_key=token_provider,
)
```

For Azure AI Vision embeddings, use `DefaultAzureCredential().get_token("https://cognitiveservices.azure.com/.default")` and send `Authorization: Bearer <token>` with `httpx`. If a target Vision API/resource does not accept Entra ID in the chosen region or SKU, fail with a clear setup error and document the required Azure-side configuration; do not silently fall back to keys.

---

## 4. Models & API Reference

Use Microsoft Learn as the source of truth during implementation, because deployment availability, pricing, regions, and preview API details change. Current implementation references:
- Azure OpenAI v1 API lifecycle: https://learn.microsoft.com/azure/foundry/openai/api-version-lifecycle
- Azure OpenAI image generation: https://learn.microsoft.com/azure/foundry/openai/how-to/dall-e
- Azure OpenAI Sora/video generation: https://learn.microsoft.com/azure/foundry/openai/concepts/video-generation
- Azure AI Vision multimodal embeddings: https://learn.microsoft.com/azure/ai-services/computer-vision/how-to/image-retrieval

All deployment names in this plan are placeholders until real deployments are provided. The SDK must load deployment names from settings and must not hard-code model availability, pricing, or regions.

### 4.1 MAI-Image-2 (Microsoft's native T2I model)

- **Capability**: Text-to-image generation ONLY (no editing/inpainting)
- **Availability / regions / pricing**: Verify in Microsoft Learn and the Foundry portal at implementation time.
- **Deployment type**: Deployment-dependent.

**API — Image Generation:**
```http
POST {AZURE_OPENAI_ENDPOINT}/openai/v1/images/generations
Authorization: Bearer <DefaultAzureCredential token>
Content-Type: application/json

{
  "model": "{MAI_IMAGE_2_DEPLOYMENT}",
  "prompt": "A red sports car on a tropical beach at sunset",
  "n": 1,
  "size": "1024x1024",        // 1024x1024, 1024x1536, 1536x1024
  "quality": "high",           // low, medium, high
  "output_format": "png"
}
```

**Response:**
```json
{
  "data": [
    {
      "b64_json": "<base64-encoded-image>",
      "revised_prompt": "..."
    }
  ]
}
```

**MAI-Image-2e** (efficient variant): Same API shape, different deployment name if available in the target subscription. Verify performance/cost claims in Foundry pricing before implementation.

### 4.2 GPT-Image-2 (OpenAI model on Azure)

- **Capability**: Generation + Editing + Inpainting + Multi-image composition
- **Status**: Public preview / availability must be verified in the target tenant.
- **Strengths**: High-resolution generation, editing/inpainting, broad aspect ratios, and strong text rendering per Microsoft Learn.

**API — Image Generation:**
```http
POST {AZURE_OPENAI_ENDPOINT}/openai/v1/images/generations
Authorization: Bearer <DefaultAzureCredential token>
Content-Type: application/json

{
  "model": "{GPT_IMAGE_2_DEPLOYMENT}",
  "prompt": "...",
  "n": 1,
  "size": "1024x1024",
  "quality": "high",
  "output_format": "png",
  "background": "auto"
}
```

**API — Image Editing (Inpainting / Composition):**
```http
POST {AZURE_OPENAI_ENDPOINT}/openai/v1/images/edits
Authorization: Bearer <DefaultAzureCredential token>

Content-Type: multipart/form-data

Fields:
  model: "{GPT_IMAGE_2_DEPLOYMENT}"
  image: <binary image file(s)>     // Up to 16 reference images
  mask: <binary PNG with alpha>     // OPTIONAL
  prompt: "Replace the background with a white studio backdrop"
  size: "1024x1024"
  quality: "medium"
  n: 1
  response_format: "b64_json"
```

**Supported input formats**: PNG (required for mask), WEBP, JPEG, non-animated GIF
**Max input file size**: 25 MB per image

### 4.3 Sora 2 (Video Generation)

- **Capability**: Text-to-video, image-to-video (up to 2 reference images), video remix, audio generation
- **Regions / pricing / access**: Gated and deployment-dependent; verify in Microsoft Learn and the Foundry portal once deployment details are available.
- **API pattern**: Async job-based — submit job → poll for completion → download output

> **⚠️ Provider risk**: Treat Sora as a swappable provider. Access, regions, pricing, and preview semantics can change; keep alternative video model research in Phase 7.

**API — Create Video (Text-to-Video):**
```http
POST {AZURE_OPENAI_ENDPOINT}/openai/v1/video/generations/jobs?api-version=preview

Headers:
  Authorization: Bearer <DefaultAzureCredential token>
  Content-Type: application/json

{
  "model": "{SORA_2_DEPLOYMENT}",
  "prompt": "A golden retriever running through a field of sunflowers at sunset, cinematic 4K",
  "width": 1920,
  "height": 1080,
  "n_seconds": 8,
  "n_variants": 1
}
```

**Response (job submitted):**
```json
{
  "id": "video_abc123",
  "status": "queued"
}
```

**Poll / Download:**
```http
GET {AZURE_OPENAI_ENDPOINT}/openai/v1/video/generations/jobs/{job_id}?api-version=preview
GET {AZURE_OPENAI_ENDPOINT}/openai/v1/video/generations/{generation_id}/content/video?api-version=preview
```

**API — Image-to-Video:**
```http
POST {AZURE_OPENAI_ENDPOINT}/openai/v1/video/generations/jobs?api-version=preview

{
  "model": "{SORA_2_DEPLOYMENT}",
  "prompt": "The car drives away down the highway",
  "width": 1920,
  "height": 1080,
  "n_seconds": 8,
  "n_variants": 1,
  "inpaint_items": [
    { "file_name": "reference.png", "frame_index": 0 }
  ]
}
```

Submit image/video inputs as multipart form-data as described in Microsoft Learn. Supported sizes/durations are deployment-dependent and must be validated against the current docs and portal configuration.

**Python SDK:**
```python
import httpx
from azure.identity import DefaultAzureCredential

token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
# Use httpx for preview video job endpoints until SDK coverage is confirmed.
```

### 4.4 Azure AI Vision — Multimodal Embeddings (for Layer 1 evaluation)

- **Model version**: 2023-04-15 (multilingual, 102 languages)
- **Capability**: Shared text-image embedding space (Florence-based, 1024-dim vectors)

**API — Vectorize Text:**
```http
POST {AZURE_VISION_ENDPOINT}/computervision/retrieval:vectorizeText?api-version=2024-02-01&model-version=2023-04-15

Headers:
  Authorization: Bearer <DefaultAzureCredential token>
  Content-Type: application/json

{ "text": "A red sports car on a tropical beach at sunset" }
```

**API — Vectorize Image:**
```http
POST {AZURE_VISION_ENDPOINT}/computervision/retrieval:vectorizeImage?api-version=2024-02-01&model-version=2023-04-15

Headers:
  Authorization: Bearer <DefaultAzureCredential token>
  Content-Type: application/octet-stream

Body: <raw image bytes>
```

**Both return:** `{ "vector": [float × 1024], "modelVersion": "2023-04-15" }`

**Constraints:** Image < 20 MB, > 10×10 px, < 16000×16000 px. Text: 1–70 words. For longer prompts, `EmbeddingEvaluator` must first create a concise visual summary (or use decomposed attributes) and record the summarized text in the score metadata.

### 4.5 Evaluation Models (vision-enabled LLMs for Layers 2 & 3)

| Model | Vision | JSON Mode | Input $/1M | Output $/1M | Context | Recommended For |
|-------|--------|-----------|------------|-------------|---------|-----------------|
| **o4-mini** | Yes | Yes | $1.10 | $4.40 | 200K | Layer 2 rubric QA + Prompt Decomposer |
| **GPT-5.4 Mini** | Yes | Yes | $0.75 | $4.50 | 400K | Layer 2 rubric QA (alternative) |
| **GPT-5.4** | Yes | Yes | $2.50 | $15.00 | 1.1M | Layer 3 LLM Judge (strong aesthetics) |
| **GPT-5.5** | Yes | Yes | $5.00 | $30.00 | 1.1M | Layer 3 LLM Judge (highest capability) |
| **GPT-5 Mini** | Yes | Yes | $0.25 | $2.00 | 400K | Budget option for Layer 2 |

**Default configuration:** Decomposer = `o4-mini`, Layer 2 = `o4-mini`, Layer 3 = `gpt-5.4`. This split cuts per-image eval cost ~50% vs. using GPT-5.5 everywhere.

**API — Chat Completions with Vision (GPT-5.x models):**
```http
POST {AZURE_OPENAI_ENDPOINT}/openai/v1/chat/completions
Authorization: Bearer <DefaultAzureCredential token>
Content-Type: application/json

{
  "model": "{DEPLOYMENT}",
  "messages": [
    { "role": "system", "content": "You are an expert image quality evaluator..." },
    { "role": "user", "content": [
        { "type": "text", "text": "Evaluate this image..." },
        { "type": "image_url", "image_url": { "url": "data:image/png;base64,{b64}" } }
    ]}
  ],
  "max_tokens": 2000,
  "temperature": 0.1,
  "response_format": { "type": "json_object" }
}
```

**API — o-series models (o3, o4-mini) — different conventions:**
```http
{
  "messages": [
    { "role": "developer", "content": "..." },    // "developer" not "system"
    { "role": "user", "content": [...] }
  ],
  "max_completion_tokens": 2000,                   // not "max_tokens"
  "reasoning_effort": "medium",                    // not "temperature"
  "response_format": { "type": "json_object" }
}
```

---

## 5. SDK: `t2i_core` Package

### 5.0 Settings and Client Construction

All providers and evaluators receive a shared `Settings` object. Settings load endpoints, deployment names, evaluation weights, and thresholds from environment variables and/or UI inputs. They do **not** load API keys by default.

```python
class Settings(BaseModel):
    azure_openai_endpoint: str
    azure_vision_endpoint: str

    mai_image_deployment: str = "mai-image-2"
    mai_image_efficient_deployment: str = "mai-image-2-efficient"
    gpt_image_deployment: str = "gpt-image-2"
    sora_deployment: str = "sora-2"

    eval_model_config: EvalModelConfig = Field(default_factory=EvalModelConfig)
    eval_thresholds: EvaluationThresholds = Field(default_factory=EvaluationThresholds)
    eval_weights: dict[str, float] = Field(default_factory=lambda: {
        "embedding_score": 0.20,
        "rubric_score": 0.45,
        "llm_judge_score": 0.35,
    })
```

Client helpers:
- `get_openai_client(settings) -> AsyncOpenAI` using `DefaultAzureCredential` + `https://ai.azure.com/.default`
- `get_vision_token() -> str` using `DefaultAzureCredential` + `https://cognitiveservices.azure.com/.default`
- `get_http_client() -> httpx.AsyncClient` for Azure AI Vision and preview video endpoints

### 5.1 Providers (Abstract Interface)

All providers implement a common interface so they're swappable:

```python
from abc import ABC, abstractmethod
from t2i_core.types import GenerationResult, EditResult, VideoResult

class ImageProvider(ABC):
    """Abstract base for image generation models."""
    
    @abstractmethod
    async def generate(self, prompt: str, size: str = "1024x1024",
                       quality: str = "high", n: int = 1) -> list[GenerationResult]: ...
    
class EditableImageProvider(ImageProvider):
    """Extended interface for models that support editing."""
    
    @abstractmethod
    async def edit(self, images: list[bytes], prompt: str,
                   mask: bytes | None = None, **kwargs) -> list[EditResult]: ...

class VideoProvider(ABC):
    """Abstract base for video generation models (async job pattern)."""
    
    @abstractmethod
    async def create_video(self, prompt: str, size: str = "1920x1080",
                           seconds: int = 8, **kwargs) -> str: ...  # returns job_id
    
    @abstractmethod
    async def poll_video(self, job_id: str) -> VideoResult: ...
    
    @abstractmethod
    async def download_video(self, job_id: str) -> bytes: ...
```

**Providers:**
- `MAIImageProvider(ImageProvider)` — MAI-Image-2 / MAI-Image-2e
- `GPTImageProvider(EditableImageProvider)` — GPT-Image-2
- `SoraVideoProvider(VideoProvider)` — Sora 2

### 5.2 Generation Scenarios

10 scenarios, each an async function in its own module with typed Pydantic input/output models.

**Summary:**

| # | Scenario | Module | Provider(s) | Description |
|---|----------|--------|-------------|-------------|
| 1 | Brand Template | `brand_template.py` | MAI / GPT | Brand guidelines + content brief → on-brand image |
| 2 | Multi-Image Composition | `multi_image_composition.py` | GPT only | 2-16 source images → composed output |
| 3 | Multi-Turn Refinement | `multi_turn_refinement.py` | GPT only | Iterative generate → refine → refine chain |
| 4 | Inpainting | `inpainting.py` | GPT only | Source image + optional mask + edit prompt |
| 5 | Product Placement | `product_placement.py` | GPT only | Product image → multiple environments |
| 6 | Batch Variations + Auto-Rank | `batch_variations.py` | MAI / GPT | N variations → evaluate → rank |
| 7 | Text Rendering | `text_rendering.py` | GPT preferred | Embedded text in images (headlines, labels) |
| 8 | Aspect Ratio Adaptation | `aspect_ratio_adaptation.py` | GPT preferred | One concept → multiple format sizes |
| 9 | Text-to-Video | `text_to_video.py` | Sora 2 | Prompt → video with platform presets |
| 10 | Image-to-Video | `image_to_video.py` | Sora 2 | 1-2 reference images → animated video |

**Detailed specs per scenario below.**

---

#### 5.2.1 Brand Template Generation

**Module:** `scenarios/brand_template.py`
**Description**: User provides brand guidelines + content brief. System composes a brand-constrained prompt and generates on-brand marketing assets.

**Implementation:**
- Accept a `BrandTemplate` object: `{ colors: ["#0078D4", "#FFFFFF"], font_style: "modern sans-serif", tone: "professional", logo_description: "blue shield icon" }`
- Compose a system prompt that embeds brand constraints before the user's content brief
- Generate using MAI-Image-2 or GPT-Image-2

**Input:** `BrandTemplate` + content brief (text)
**Output:** Generated image(s) + the composed prompt used
**Model:** MAI-Image-2 (pure generation) or GPT-Image-2

---

#### 5.2.2 Multi-Image Composition

**Module:** `scenarios/multi_image_composition.py`
**Description**: Combine multiple source images (product photo + background + overlay) into a single composed output.

**Implementation:**
- Accept 2–16 reference images + a composition prompt
- Use GPT-Image-2 `/images/edits` endpoint with multiple `image` fields
- Prompt describes how to combine them

**Input:** List of image files (2–16) + composition prompt
**Output:** Composed image
**Model:** GPT-Image-2 ONLY (MAI-Image-2 does not support image input)

---

#### 5.2.3 Multi-Turn Refinement

**Module:** `scenarios/multi_turn_refinement.py`
**Description**: Iterative conversation — generate, then refine based on feedback.

**Implementation:**
- Maintain a `ConversationHistory` with the last generated image + prior instructions
- Each turn: take previous output image + new instruction → call `/images/edits`
- Track the full chain of refinements

**Input:** Initial prompt, then sequence of refinement instructions
**Output:** Image at each step + full conversation log
**Model:** GPT-Image-2 (needs image input for refinement)

---

#### 5.2.4 Inpainting / Selective Edit

**Module:** `scenarios/inpainting.py`
**Description**: Modify a specific region of an existing image — change background, swap product, remove object.

**Implementation:**
- Accept source image + optional PNG mask + edit prompt
- If no mask provided, rely on GPT-Image-2's prompt-based region inference
- Call `/images/edits` with mask (if provided)

**Input:** Source image + optional mask (PNG with alpha) + edit prompt
**Output:** Edited image
**Model:** GPT-Image-2 ONLY

---

#### 5.2.5 Product Placement

**Module:** `scenarios/product_placement.py`
**Description**: Place a product photo into different environments (beach, store shelf, kitchen counter).

**Implementation:**
- Accept product image + list of environment descriptions
- For each environment: call `/images/edits` with product image + environment prompt
- Batch generate across environments

**Input:** Product image + list of environment prompts
**Output:** One image per environment
**Model:** GPT-Image-2

---

#### 5.2.6 Batch Variations + Auto-Rank

**Module:** `scenarios/batch_variations.py`
**Description**: Generate N variations of the same concept, run all through the evaluation pipeline, auto-pick the best.

**Implementation:**
- Accept prompt + `n` (number of variations, 1–10)
- Call image generation with `n` parameter
- Run each output through the full evaluation pipeline (or selected layers)
- Sort by composite score, return ranked results

**Input:** Prompt + n (count) + optional evaluation config (layers, preset)
**Output:** Ranked list of images with full evaluation reports
**Model:** MAI-Image-2 or GPT-Image-2 (user choice)

---

#### 5.2.7 Text Rendering

**Module:** `scenarios/text_rendering.py`
**Description**: Generate images containing embedded text — headlines, product labels, event posters.

**Implementation:**
- Accept text content + visual context prompt
- Generate image
- Evaluate text legibility as part of evaluation (Layer 3 criterion)

**Input:** Text to embed + visual prompt
**Output:** Generated image
**Model:** GPT-Image-2 preferred for text rendering; verify exact model capability in current Microsoft Learn docs.

---

#### 5.2.8 Aspect Ratio Adaptation

**Module:** `scenarios/aspect_ratio_adaptation.py`
**Description**: Same concept, different formats — Instagram square, LinkedIn banner, mobile story, desktop hero.

**Implementation:**
- Accept concept prompt + list of target formats
- Map format names to pixel sizes:
  - `instagram_square`: 1024×1024
  - `instagram_story`: 1024×1536
  - `linkedin_banner`: 1536×1024
  - `desktop_hero`: 2000×1000
  - `mobile_story`: 667×2000
- Generate one image per format

**Input:** Concept prompt + list of format names
**Output:** One image per format
**Model:** GPT-Image-2 (broadest size support, arbitrary resolutions)

---

#### 5.2.9 Text-to-Video Generation

**Module:** `scenarios/text_to_video.py`
**Description**: Generate short video clips from text prompts — product demos, social media content, concept visualization.

**Implementation:**
- Accept a text prompt + video parameters (size, duration)
- Call Sora 2 `/v1/videos` endpoint
- Poll for completion (async job pattern) — exponential backoff with configurable timeout
- Download and save MP4 file
- Support batch generation: same prompt across different sizes/durations for platform adaptation

**Input:** Text prompt + size (default 1920×1080) + duration (4/8/12s) + optional platform preset
**Output:** MP4 video file(s)
**Model:** Sora 2 ONLY

**Platform presets:**
- `instagram_reel`: 1080×1920 (9:16), 8s
- `youtube_short`: 1080×1920 (9:16), 12s
- `linkedin_video`: 1920×1080 (16:9), 8s
- `square_social`: 1024×1024 (1:1), 8s
- `preview`: 480×480 (1:1), 4s (cheapest for quick iteration)

---

#### 5.2.10 Image-to-Video Animation

**Module:** `scenarios/image_to_video.py`
**Description**: Animate a static image (product photo, illustration, hero image) into a short video clip.

**Implementation:**
- Accept 1–2 reference images + a motion/action prompt
- Call Sora 2 `/v1/videos` with `input_reference` containing the image(s)
- Poll and download as above
- Common use cases: product turntable, hero image parallax, illustration coming to life

**Input:** 1–2 reference images + motion prompt + size + duration
**Output:** MP4 video file
**Model:** Sora 2 ONLY

> **⚠️ Note on video evaluation**: The 3-layer evaluation pipeline is designed for images. Video evaluation (temporal coherence, motion quality, audio-visual sync) is out of scope for the initial build. See Phase 7 for planned research.

### 5.3 Evaluation Module — Individual Techniques

**This is the critical design requirement.** Each evaluation technique is a **standalone evaluator** that can be invoked independently. The pipeline (Section 5.4) orchestrates all three, but callers can use any one alone.

```python
from t2i_core.evaluation import (
    EmbeddingEvaluator,     # Layer 1 — standalone
    RubricEvaluator,        # Layer 2 — standalone
    LLMJudgeEvaluator,      # Layer 3 — standalone
    PromptDecomposer,       # Shared utility
    EvaluationPipeline,     # Full 3-layer orchestrator
    EvalModelConfig,        # Model configuration
    EvalPreset,             # Preset enum
)
```

#### 5.3.1 EmbeddingEvaluator (Layer 1 — SigLIP-style)

**What it measures**: Overall semantic alignment — "is it in the right ballpark?"

```python
class EmbeddingEvaluator:
    """Standalone Layer 1 evaluator. Uses Azure AI Vision multimodal embeddings."""
    
    async def evaluate(self, image: bytes, prompt: str) -> EmbeddingScore:
        """Run embedding similarity evaluation independently."""
        vector_prompt = await self._prepare_embedding_prompt(prompt)
        text_vec = await self._vectorize_text(vector_prompt)
        image_vec = await self._vectorize_image(image)
        similarity = cosine_similarity(text_vec, image_vec)
        return EmbeddingScore(
            text_vector=text_vec,
            image_vector=image_vec,
            cosine_similarity=similarity,
            vectorized_text=vector_prompt,
            model_version="2023-04-15"
        )
```

**Output:** `EmbeddingScore` — cosine similarity 0.0–1.0
**Performance**: ~50-100ms, ~$0.001/image
**Default threshold**: < 0.50 = significant semantic misalignment. This is configurable in `EvaluationThresholds` and in the Streamlit UI.
**Long prompts**: Azure AI Vision text vectorization accepts 1–70 words. If the prompt is longer, summarize it into a concise visual description before vectorization and store that summary in `EmbeddingScore.vectorized_text`.

#### 5.3.2 RubricEvaluator (Layer 2 — Gecko-style)

**What it measures**: Factual completeness — "did the image include everything the prompt asked for?"

```python
class RubricEvaluator:
    """Standalone Layer 2 evaluator. Decomposes prompt → QA pairs → vision LLM scoring."""
    
    def __init__(self, model_config: EvalModelConfig | None = None):
        self.config = model_config or EvalModelConfig()
        self.decomposer = PromptDecomposer(
            deployment=self.config.decomposer_deployment,
            is_o_series=self.config.decomposer_is_o_series
        )
    
    async def evaluate(self, image: bytes, prompt: str,
                       attributes: list[Attribute] | None = None) -> RubricScore:
        """Run rubric evaluation independently.
        
        Args:
            image: Image bytes
            prompt: Original generation prompt
            attributes: Pre-decomposed attributes (optional — will decompose if not provided)
        """
        if attributes is None:
            attributes = await self.decomposer.decompose(prompt)
        # ... batched QA evaluation against image ...
        return RubricScore(...)
```

**Implementation detail**: Decomposes prompt into atomic attributes → generates verification questions → sends batched QA + image to vision LLM → aggregates yes/no/partial answers.

**System prompt for QA evaluation:**
```
You are a precise image evaluator. Answer each question about the image.
Return JSON: { "results": [{ "answer": "yes"|"no"|"partial", "confidence": 0.0-1.0, "reasoning": "..." }] }
```

**Output:**
```python
class AttributeResult(BaseModel):
    category: str                   # object, color, action, setting, etc.
    description: str                # "red car"
    question: str                   # "Is the car red?"
    answer: Literal["yes", "no", "partial"]
    confidence: float               # 0.0 to 1.0
    reasoning: str

class RubricScore(BaseModel):
    attributes: list[AttributeResult]
    total_attributes: int
    matched_attributes: int         # count of "yes"
    partial_attributes: int         # count of "partial"
    rubric_score: float             # 0.0 to 1.0 (yes=1, partial=0.5, no=0)
```

**Performance**: ~2-5s, ~$0.01-0.03/image

#### 5.3.3 LLMJudgeEvaluator (Layer 3 — LLM-as-Judge)

**What it measures**: Holistic subjective quality — "how good does it actually look?"
**Design principle**: Criteria MUST NOT overlap with Layer 2. No prompt adherence — that's Layer 2's job.

```python
class LLMJudgeEvaluator:
    """Standalone Layer 3 evaluator. Likert 1-5 scoring on quality dimensions."""
    
    def __init__(self, model_config: EvalModelConfig | None = None):
        self.config = model_config or EvalModelConfig()
    
    async def evaluate(self, image: bytes, prompt: str) -> LLMJudgeScore:
        """Run LLM judge evaluation independently."""
        # ... single vision LLM call with scoring rubric ...
        return LLMJudgeScore(...)
```

**Criteria (1-5 Likert each):**

| Criterion | What it assesses | 1 (Worst) | 5 (Best) |
|-----------|-----------------|-----------|----------|
| **Visual Quality** | Artifacts, distortions, noise, blur | Major artifacts, unusable | Clean, no visible artifacts |
| **Spatial Coherence** | Physics, layout, perspective, shadows | Impossible geometry | Fully coherent scene |
| **Style Fidelity** | Matches requested artistic style | Wrong style entirely | Perfect style match |
| **Aesthetic Appeal** | Composition, color harmony, impact | Poor composition | Striking, well-composed |
| **Text Legibility** | Rendered text accuracy (skip if N/A) | Garbled, unreadable | Perfect, legible |

**Output:**
```python
class CriterionScore(BaseModel):
    score: int                      # 1-5
    justification: str

class LLMJudgeScore(BaseModel):
    visual_quality: CriterionScore
    spatial_coherence: CriterionScore
    style_fidelity: CriterionScore
    aesthetic_appeal: CriterionScore
    text_legibility: CriterionScore | None   # None if no text in prompt
    overall_impression: str
    average_score: float            # mean of all applicable scores
```

**Performance**: ~3-5s, ~$0.01-0.03/image

#### 5.3.4 PromptDecomposer (Shared Utility)

Used by RubricEvaluator and available standalone for any caller:

```python
class PromptDecomposer:
    """Breaks a text prompt into atomic visual attributes."""
    
    async def decompose(self, prompt: str) -> list[Attribute]:
        """Returns independently verifiable attributes. Cached per prompt."""
```

**System prompt:**
```
Decompose the following image generation prompt into a list of atomic visual attributes.
Each attribute should be independently verifiable in a generated image.
Return JSON: { "attributes": [{ "category": "object|color|action|setting|lighting|style|text|count", "description": "..." }] }
```

### 5.4 Evaluation Module — Full Pipeline

The `EvaluationPipeline` orchestrates all three layers with configurable weights. It also supports **selective layer execution**.

```python
class EvaluationPipeline:
    """Orchestrates the 3-layer evaluation pipeline."""
    
    def __init__(self, model_config: EvalModelConfig | None = None,
                 weights: dict[str, float] | None = None):
        self.config = model_config or EvalModelConfig()
        self.weights = weights or {
            "embedding_score": 0.20,
            "rubric_score": 0.45,
            "llm_judge_score": 0.35
        }
        # Initialize individual evaluators (reused, not duplicated)
        self.embedding = EmbeddingEvaluator()
        self.rubric = RubricEvaluator(model_config=self.config)
        self.judge = LLMJudgeEvaluator(model_config=self.config)
    
    async def evaluate(self, image: bytes, prompt: str,
                       layers: list[str] | None = None) -> EvaluationReport:
        """Run evaluation pipeline.
        
        Args:
            image: Image bytes
            prompt: Original generation prompt
            layers: Which layers to run. Default None = all three.
                    Options: ["embedding"], ["rubric"], ["judge"],
                    ["embedding", "rubric"], ["embedding", "judge"], etc.
        """
        layers = layers or ["embedding", "rubric", "judge"]
        
        embedding_result = await self.embedding.evaluate(image, prompt) if "embedding" in layers else None
        rubric_result = await self.rubric.evaluate(image, prompt) if "rubric" in layers else None
        judge_result = await self.judge.evaluate(image, prompt) if "judge" in layers else None
        
        composite = self._compute_composite(embedding_result, rubric_result, judge_result)
        
        return EvaluationReport(
            prompt=prompt, embedding=embedding_result,
            rubric=rubric_result, llm_judge=judge_result,
            composite_score=composite, weights=self.weights, ...
        )
```

**Composite formula:**
```python
composite = (
    sum(weight * score for weight, score in active_weighted_scores) /
    sum(weight for weight, _ in active_weighted_scores)
)
# Only include layers that actually ran. Do not add zeroes for skipped layers.
```

**Full EvaluationReport schema:**
```python
class EvaluationReport(BaseModel):
    prompt: str
    model_used: str
    image_path: str
    layers_run: list[str]           # Which layers were executed
    
    embedding: EmbeddingScore | None
    rubric: RubricScore | None
    llm_judge: LLMJudgeScore | None
    
    weights: dict[str, float]
    composite_score: float          # 0.0 to 1.0
    
    generation_time_ms: int
    evaluation_time_ms: int
    total_cost_estimate: float
    threshold_decision: Literal["accept", "review", "regenerate"]
    threshold_reasons: list[str]
    timestamp: datetime
```

### 5.5 Evaluation Model Configuration (Presets)

```python
class EvalPreset(str, Enum):
    COST_OPTIMIZED = "cost_optimized"       # DEFAULT
    UNIFIED_PREMIUM = "unified_premium"     # GPT-5.5 for everything
    UNIFIED_BALANCED = "unified_balanced"   # GPT-5.4 for everything
    BUDGET = "budget"                       # Cheapest vision-capable models
    CUSTOM = "custom"                       # User picks each model

class EvalModelConfig(BaseModel):
    preset: EvalPreset = EvalPreset.COST_OPTIMIZED
    decomposer_deployment: str = "o4-mini"
    rubric_deployment: str = "o4-mini"
    judge_deployment: str = "gpt-5.4"
    decomposer_is_o_series: bool = True
    rubric_is_o_series: bool = True
    judge_is_o_series: bool = False

    @classmethod
    def from_preset(cls, preset: EvalPreset) -> "EvalModelConfig":
        presets = {
            EvalPreset.COST_OPTIMIZED: dict(
                decomposer_deployment="o4-mini", rubric_deployment="o4-mini",
                judge_deployment="gpt-5.4",
                decomposer_is_o_series=True, rubric_is_o_series=True, judge_is_o_series=False),
            EvalPreset.UNIFIED_PREMIUM: dict(
                decomposer_deployment="gpt-5.5", rubric_deployment="gpt-5.5",
                judge_deployment="gpt-5.5",
                decomposer_is_o_series=False, rubric_is_o_series=False, judge_is_o_series=False),
            EvalPreset.UNIFIED_BALANCED: dict(
                decomposer_deployment="gpt-5.4", rubric_deployment="gpt-5.4",
                judge_deployment="gpt-5.4",
                decomposer_is_o_series=False, rubric_is_o_series=False, judge_is_o_series=False),
            EvalPreset.BUDGET: dict(
                decomposer_deployment="o4-mini", rubric_deployment="gpt-5-mini",
                judge_deployment="gpt-5.4-mini",
                decomposer_is_o_series=True, rubric_is_o_series=False, judge_is_o_series=False),
        }
        return cls(preset=preset, **presets[preset])

class EvaluationThresholds(BaseModel):
    """Defaults are best-effort starting points; expose them in the UI."""
    embedding_min: float = 0.50
    rubric_min: float = 0.70
    judge_min_average: float = 3.50
    composite_accept: float = 0.70
    composite_regenerate: float = 0.55
```

| Preset | Decomposer | Layer 2 | Layer 3 | Cost/Image | Quality |
|--------|-----------|---------|---------|------------|---------|
| **Cost Optimized** (default) | o4-mini | o4-mini | GPT-5.4 | ~$0.02 | High |
| **Unified Premium** | GPT-5.5 | GPT-5.5 | GPT-5.5 | ~$0.06 | Highest |
| **Unified Balanced** | GPT-5.4 | GPT-5.4 | GPT-5.4 | ~$0.04 | Very good |
| **Budget** | o4-mini | GPT-5 Mini | GPT-5.4 Mini | ~$0.01 | Good enough for batch screening |

**`is_o_series` flag controls:** `role: "developer"` vs `"system"`, `max_completion_tokens` vs `max_tokens`, `reasoning_effort` vs `temperature`.
**Env override:** If `EVAL_UNIFIED_DEPLOYMENT` is set, it overrides the preset for all layers.

**Threshold policy:** The SDK returns a decision label:
- `accept` when composite score >= `composite_accept` and no individual layer is below its configured minimum
- `review` when composite score is between `composite_regenerate` and `composite_accept`
- `regenerate` when composite score < `composite_regenerate` or a required layer falls below its configured minimum

The Streamlit app must expose these thresholds in the evaluation sidebar so users can tune strictness per workflow.

---

## 6. Skills (microsoft/skills Standard Format)

Skills are the agent-facing knowledge layer. They follow the [skill-creator guide](https://github.com/microsoft/skills/blob/main/.github/skills/skill-creator/SKILL.md):
- YAML frontmatter with `name` and `description` (description = trigger mechanism)
- SKILL.md body < 500 lines — concise, only what the agent doesn't already know
- `references/` for detailed API docs and patterns
- `scripts/` for deterministic CLI operations that import from `t2i_core`

Publishing target: public GitHub repository. The skills must not require secrets or tenant-specific URLs. They should document that users clone the repo and install the local SDK in editable mode until a package publishing strategy exists.

### 6.1 Skill: `t2i-generation`

**Frontmatter:**
```yaml
---
name: t2i-generation
description: |
  Generate images and videos using Azure Foundry models (MAI-Image-2, GPT-Image-2, Sora 2).
  Supports 10 scenarios: brand templates, multi-image composition, inpainting, product placement,
  text rendering, aspect ratio adaptation, batch variations, multi-turn refinement,
  text-to-video, and image-to-video.
  USE FOR: "generate image", "create hero image", "product photo", "brand asset",
  "marketing visual", "text to video", "animate this image", "create social media assets".
  DO NOT USE FOR: image evaluation, quality scoring, or design review.
---
```

**SKILL.md body** covers:
1. Installation from local checkout (`pip install -e packages/t2i_core` from repo root; no PyPI publishing assumed)
2. Environment variables
3. Authentication (OpenAI SDK v1 client + DefaultAzureCredential pattern)
4. Quick start — generate an image in 5 lines
5. Scenario table — which scenario to use for which task
6. Model selection guide — MAI vs GPT-Image-2 vs Sora 2
7. Best practices (error handling, content filters, cost awareness)

**`scripts/generate.py`** — CLI entry point:
```bash
# Image generation
python generate.py --scenario brand_template --prompt "..." --brand-config brand.json
python generate.py --scenario inpainting --image source.png --mask mask.png --prompt "..."
python generate.py --scenario batch_variations --prompt "..." --n 5 --model gpt-image-2
python generate.py --scenario aspect_ratio --prompt "..." --formats instagram_square,linkedin_banner

# Video generation
python generate.py --scenario text_to_video --prompt "..." --preset instagram_reel
python generate.py --scenario image_to_video --image product.png --prompt "..." --seconds 8
```

**`references/`:**
- `mai-image-api.md` — full MAI-Image-2 API patterns, sizes, quality levels
- `gpt-image-api.md` — generation + editing API patterns, multipart/form-data, mask usage
- `sora-video-api.md` — async job pattern, polling, platform presets, provider-risk notes
- `scenarios.md` — detailed per-scenario recipes with code examples

### 6.2 Skill: `t2i-evaluation`

**Frontmatter:**
```yaml
---
name: t2i-evaluation
description: |
  Evaluate image quality using individual techniques or a full 3-layer pipeline.
  Layer 1 (Embedding): Fast semantic alignment via Azure AI Vision cosine similarity.
  Layer 2 (Rubric): Prompt decomposition into atomic attributes + binary QA scoring.
  Layer 3 (LLM Judge): Likert 1-5 scoring on visual quality, coherence, style, aesthetics.
  Full Pipeline: All 3 layers + composite score with configurable weights.
  USE FOR: "evaluate image quality", "score this image", "is this good enough",
  "compare images", "rank variations", "check prompt adherence", "quality gate".
  DO NOT USE FOR: image generation, video creation, or UI code review.
---
```

**SKILL.md body** covers:
1. Installation from local checkout (`pip install -e packages/t2i_core` from repo root; no PyPI publishing assumed)
2. Environment variables
3. Which evaluation to use when (decision tree):
   - **Fast check** → Embedding only (50ms, $0.001)
   - **Prompt adherence** → Rubric only ($0.01-0.03)
   - **Quality assessment** → LLM Judge only ($0.01-0.03)
   - **Full quality gate** → Pipeline (all 3 + composite score)
   - **Custom combination** → Pipeline with `layers=["embedding", "judge"]`
4. Preset selection guide
5. Interpreting scores (thresholds, what to do with low scores)

**`scripts/evaluate.py`** — CLI entry point supporting individual OR pipeline:
```bash
# Individual evaluation techniques
python evaluate.py --image hero.png --prompt "..." --layer embedding
python evaluate.py --image hero.png --prompt "..." --layer rubric
python evaluate.py --image hero.png --prompt "..." --layer judge

# Selective combination
python evaluate.py --image hero.png --prompt "..." --layers embedding,rubric

# Full 3-layer pipeline
python evaluate.py --image hero.png --prompt "..." --pipeline
python evaluate.py --image hero.png --prompt "..." --pipeline --preset unified_premium

# Batch evaluation
python evaluate.py --images-dir ./outputs/ --prompt "..." --pipeline --output results.json
```

**`references/`:**
- `embedding-layer.md` — Azure AI Vision API, cosine similarity, threshold calibration
- `rubric-layer.md` — prompt decomposition, QA generation, batched evaluation, system prompts
- `judge-layer.md` — Likert criteria, system prompt, scoring calibration
- `composite-scoring.md` — weight config, composite formula, re-normalization for partial layers
- `eval-presets.md` — all presets with cost/quality tradeoffs

### 6.3 Skill: `t2i-design-assets`

**Frontmatter:**
```yaml
---
name: t2i-design-assets
description: |
  End-to-end visual asset creation: generate images/videos, evaluate quality,
  and adapt for multiple platforms. Chains generation + evaluation + adaptation
  into common workflows.
  USE FOR: "create design assets", "brand images for my UI", "hero image for landing page",
  "social media package", "generate and pick the best", "production-ready visuals".
  DO NOT USE FOR: evaluation only (use t2i-evaluation), generation only (use t2i-generation),
  or UI code review (use frontend-design-review).
---
```

**SKILL.md body** covers:
1. Installation from local checkout (`pip install -e packages/t2i_core` from repo root; no PyPI publishing assumed)
2. Common workflows:
   - **Single asset with quality gate**: generate → evaluate → accept or regenerate
   - **Best-of-N selection**: generate N → evaluate all → rank → return best
   - **Multi-platform package**: generate → adapt to formats → evaluate each
   - **Brand-consistent suite**: brand template → generate variations → evaluate → rank
   - **Animated hero**: generate image → image-to-video → download
3. How this skill relates to `t2i-generation` and `t2i-evaluation` (it chains them)
4. How this complements `frontend-design-review` (that skill reviews UI code; this creates visual assets)

**`scripts/create_assets.py`** — CLI entry point:
```bash
# Generate + evaluate + pick best
python create_assets.py --workflow best_of_n --prompt "..." --n 5 --min-score 0.7

# Multi-platform package
python create_assets.py --workflow multi_platform --prompt "..." \
    --formats instagram_square,linkedin_banner,mobile_story

# Brand asset suite
python create_assets.py --workflow brand_suite --brand-config brand.json \
    --prompts prompts.json --evaluate --rank

# Image + video package
python create_assets.py --workflow social_package --prompt "..." \
    --image-formats instagram_square --video-preset instagram_reel
```

---

## 7. App UI Design (Streamlit)

### Page 1: Image Generate
- Model selector: MAI-Image-2, MAI-Image-2e, GPT-Image-2
- Scenario selector: 8 image scenarios from Section 5.2
- Dynamic input form based on scenario
- Generate → gallery display
- "Evaluate" button per image → sends to evaluation

### Page 2: Video Generate
- Text prompt for text-to-video
- Image upload for image-to-video
- Platform preset dropdown + custom size/duration controls
- Async progress bar → video player
- Download MP4 button + cost display

### Page 3: Evaluate
- **Evaluation mode selector**: "Full Pipeline", "Embedding Only", "Rubric Only", "LLM Judge Only", or custom layer combination
- **Preset selector** in sidebar (Cost Optimized, Unified Premium, etc.)
- **Threshold controls** in sidebar: embedding minimum, rubric minimum, judge minimum average, composite accept, composite regenerate
- Upload image + provide prompt
- Display results per selected layers:
  - Layer 1: Cosine similarity gauge
  - Layer 2: Per-attribute checklist + confidence bars
  - Layer 3: Radar chart (5 axes)
  - Composite: Score with weight breakdown
- When running individual layers, show only that layer's visualization

### Page 4: Compare
- Side-by-side 2-4 images, same prompt
- Full or partial evaluation per image
- Winner highlighted per criterion + overall

### Page 5: Batch Rank
- Prompt + N variations (1-10)
- Generate → auto-evaluate → ranked grid
- Export JSON/CSV

---

## 8. Implementation Phases

### Phase 1: SDK Foundation (Week 1)

**Deliverables:** `t2i_core` package scaffold with base providers, Layer 1 evaluation, types, utils.

**Tasks:**
1. Set up monorepo with `pyproject.toml` — single `t2i_core` package
2. Implement `providers/base.py` — abstract `ImageProvider`, `EditableImageProvider`, `VideoProvider`
3. Implement `providers/mai_image.py` — MAI-Image-2/2e via OpenAI SDK v1 client
4. Implement `evaluation/embedding.py` — `EmbeddingEvaluator` as standalone class
5. Implement `types.py` — all Pydantic models (generation + evaluation)
6. Implement `utils.py` — image I/O, base64, auth helpers
7. Write unit tests with mocked API responses

### Phase 2: Full Generation + GPT-Image-2 (Week 2)

**Deliverables:** GPT-Image-2 provider, all 8 image scenarios, sample data.

**Tasks:**
1. Implement `providers/gpt_image.py` — generation + editing via OpenAI SDK v1 client
2. Implement all 8 image scenario modules in `scenarios/`
3. Create `samples/` — brand templates, reference images, `sample_prompts.json`

### Phase 3: Full Evaluation Pipeline (Week 3)

**Deliverables:** All 3 evaluation layers as standalone evaluators + pipeline orchestrator.

**Tasks:**
1. Implement `evaluation/decomposer.py` — `PromptDecomposer` (standalone, cacheable)
2. Implement `evaluation/rubric.py` — `RubricEvaluator` (standalone, accepts optional pre-decomposed attributes)
3. Implement `evaluation/judge.py` — `LLMJudgeEvaluator` (standalone)
4. Implement `evaluation/pipeline.py` — `EvaluationPipeline` with selective layer execution (`layers=` param)
5. Implement `evaluation/config.py` — `EvalModelConfig` + all presets
6. Write evaluation tests — individual evaluator tests + pipeline integration tests

### Phase 4: Video Generation (Week 4)

**Deliverables:** Sora 2 provider, video scenarios, platform presets.

**Tasks:**
1. Implement `providers/sora_video.py` — async job lifecycle using Microsoft Learn preview video endpoints
2. Implement `scenarios/text_to_video.py` and `scenarios/image_to_video.py`
3. Add exponential backoff polling, cost tracking, timeout handling, and clear provider-availability errors
4. Keep `VideoProvider` abstract so alternate providers can replace Sora later

### Phase 5: Skills (Week 5)

**Deliverables:** 3 skills in microsoft/skills standard format.

**Tasks:**
1. Write `skills/t2i-generation/SKILL.md` — frontmatter, installation, scenarios, model guide
2. Write `skills/t2i-generation/scripts/generate.py` — CLI wrapper importing `t2i_core`
3. Write `skills/t2i-generation/references/` — per-model API docs, scenario recipes
4. Write `skills/t2i-evaluation/SKILL.md` — decision tree, individual vs pipeline usage
5. Write `skills/t2i-evaluation/scripts/evaluate.py` — CLI with `--layer` and `--pipeline` flags
6. Write `skills/t2i-evaluation/references/` — per-layer docs, presets, scoring guide
7. Write `skills/t2i-design-assets/SKILL.md` — workflows, chaining patterns
8. Write `skills/t2i-design-assets/scripts/create_assets.py` — workflow CLI
9. Validate all skills against skill-creator guidelines (< 500 lines, proper frontmatter, progressive disclosure)

### Phase 6: Web App (Week 6)

**Deliverables:** Streamlit app with all 5 pages, consuming `t2i_core` SDK.

**Tasks:**
1. Build `app.py` with navigation
2. Image Generate page — dynamic scenario forms
3. Video Generate page — Sora 2 async polling + video player
4. Evaluate page — **layer selector** (individual technique OR full pipeline)
5. Expose evaluation thresholds and weights in the sidebar
6. Compare + Batch Rank pages
7. Plotly radar charts for Layer 3

### Phase 7: Research — Alternative Video Models & Video Evaluation (Week 7+)

> **Research-only** — no code deliverables. Prepares for Sora 2 provider risk and video evaluation.

**Research Area 1: Alternative Video Models**

Because Sora access, pricing, regions, and preview semantics can change, evaluate:
- Runway Gen-4 / Gen-4 Turbo — Azure Foundry availability
- Stability AI (Stable Video Diffusion) — Foundry model catalog
- Microsoft MAI-Video (if announced)
- Pika, Kling, Vidu — monitor Foundry availability
- Open-source: CogVideoX, Mochi — Azure ML self-hosting

**Deliverable**: Model comparison matrix + recommendation.

**Research Area 2: Video Evaluation Pipeline**

Dimensions not covered by the image pipeline:
- Temporal coherence (object consistency across frames)
- Motion quality (smooth, physically plausible)
- Audio-visual sync
- Prompt-to-video adherence (action/narrative, not single-frame)

**Approaches to evaluate:**
1. Frame sampling + existing image pipeline + temporal consistency layer
2. Video-native vision LLMs (GPT-5.x with video understanding)
3. Specialized metrics: FVD, CLIP-FVD, VBench

**Deliverable**: Video evaluation design document.

---

## 9. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Single SDK (`t2i_core`) | Merged generation + evaluation into one package | Eliminates code duplication; skills and app both import from one source of truth |
| SDK + Skills (not skills-only) | Skills reference the SDK, don't duplicate code | Avoids 3-way script duplication; skills are thin knowledge wrappers |
| Evaluation: individual + pipeline | Each layer is a standalone class; pipeline orchestrates | Skills can invoke `--layer embedding` OR `--pipeline` — maximum flexibility |
| Selective layer execution | `EvaluationPipeline(layers=["embedding", "rubric"])` | Callers pay only for the layers they need; composite auto-renormalizes weights |
| Configurable evaluation thresholds | Defaults in SDK, controls in Streamlit UI | Users can tune quality gates per workflow without code changes |
| 3 skills, not 1 mega-skill | Separate generation / evaluation / orchestration | Each triggers independently; a coding agent needing only eval doesn't load generation docs |
| microsoft/skills format | SKILL.md + references/ + scripts/ | Standard format any coding agent recognizes; compatible with microsoft/skills repo |
| Local package, no PyPI initially | `pip install -e packages/t2i_core` | Development and public skills repo work without a publishing pipeline |
| Azure AD auth only by default | `DefaultAzureCredential` for OpenAI/Foundry and Vision | Avoids secrets in `.env`; supports local `az login`, managed identity, and workload identity |
| Complements frontend-design-review | Different scope — visual assets vs UI code | A frontend agent uses both: our skills for images, frontend-design-review for code quality |
| Different models per eval layer | o4-mini for Layer 2, GPT-5.4 for Layer 3 | Binary QA doesn't need frontier reasoning; aesthetic judgment does. ~50% cost savings |
| Batch QA in Layer 2 | Single LLM call per image, not one per attribute | 5-10x faster and cheaper |
| Layer 3 excludes prompt adherence | No overlap with Layer 2 | Layer 2 already covers factual completeness; Layer 3 focuses on quality/aesthetics |
| Sora 2 behind abstract VideoProvider | Swappable when provider availability or strategy changes | Provider abstraction allows drop-in replacement |
| Video before skills/app | Video provider lands before skills and UI consume video features | Avoids publishing skills or app pages that call unavailable SDK surfaces |

---

## 10. Dependencies

```toml
# packages/t2i_core/pyproject.toml
[project]
name = "t2i-core"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "openai>=1.50.0",
    "azure-identity>=1.17.0",
    "httpx>=0.27.0",
    "pydantic>=2.0",
    "numpy>=1.26",
    "pillow>=10.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
app = [
    "streamlit>=1.35",
    "plotly>=5.20",
    "pandas>=2.2",
]
```

---

## 11. Testing Strategy

- **Unit tests**: Mock all API calls. Verify prompt composition, score calculations, schema validation. Test each evaluator individually AND through the pipeline.
- **Individual evaluator tests**: Verify `EmbeddingEvaluator`, `RubricEvaluator`, `LLMJudgeEvaluator` each return correct schemas when called standalone.
- **Pipeline tests**: Verify `EvaluationPipeline` with `layers=` parameter — full pipeline, single layer, and partial combinations.
- **Integration tests**: Hit real Azure endpoints. Mark as `@pytest.mark.integration`.
- **Evaluation calibration**: 10 known-good + 10 known-bad image-prompt pairs. Validate default thresholds (`embedding_min=0.50`, `rubric_min=0.70`, `judge_min_average=3.50`, `composite_accept=0.70`, `composite_regenerate=0.55`) and keep them user-configurable.
- **Skill script tests**: Verify each `scripts/*.py` CLI runs end-to-end with mocked SDK calls.

---

## 12. Notes for the Coding Agent

1. **Start with Phase 1.** Get `t2i_core` scaffold + EmbeddingEvaluator working before adding scenarios.
2. **Use the OpenAI Python SDK v1 client** (`AsyncOpenAI`) with `base_url="{AZURE_OPENAI_ENDPOINT}/openai/v1/"` and `DefaultAzureCredential` token provider for supported Foundry/OpenAI calls.
3. **For Azure AI Vision embeddings** (Layer 1), use `httpx` directly with `DefaultAzureCredential` bearer tokens.
4. **Use bytes internally for images.** Encode/decode base64 only at provider/API boundaries.
5. **GPT-Image-2 editing** uses `multipart/form-data`. Prefer the OpenAI SDK v1 image edit helper if it supports the required Azure endpoint; otherwise use `httpx` with the same auth helper.
6. **o-series API differences**: `role: "developer"` not `"system"`, `max_completion_tokens` not `max_tokens`, `reasoning_effort` not `temperature`. The `is_o_series` flag in `EvalModelConfig` controls this.
7. **Structured JSON output**: `response_format={"type": "json_object"}` for all evaluation calls.
8. **Each evaluator must be independently importable and usable.** `EmbeddingEvaluator()`, `RubricEvaluator()`, `LLMJudgeEvaluator()` each work without the pipeline. The pipeline reuses them — doesn't wrap different code.
9. **Selective layer execution**: `EvaluationPipeline(layers=["embedding"])` must skip the other layers entirely (no API calls, no cost). Composite score re-normalizes to active weights only.
10. **Cost tracking**: Each evaluator tracks its own cost. Pipeline sums them. Log in `EvaluationReport`.
11. **Sora 2 async polling**: Submit → poll with exponential backoff (2s start, 30s max, 5min timeout) → download MP4. Use Microsoft Learn preview video endpoints with `httpx` unless the OpenAI SDK has confirmed support.
12. **Sora 2 provider risk**: `sora_video.py` implements `VideoProvider` interface — swappable when availability, preview semantics, or model strategy changes.
13. **Video files are MP4.** Use `st.video()` in Streamlit. Don't convert frames to base64.
14. **Skill scripts import from `t2i_core`** — they're thin CLI wrappers, not standalone implementations. Never duplicate SDK logic into scripts.
15. **Skills must follow microsoft/skills format**: YAML frontmatter, < 500 lines SKILL.md, detail goes in `references/`. Description is the trigger mechanism.
16. **The `samples/` directory**: 2 brand template JSONs, 3 product reference images (PNG), `sample_prompts.json` with 3-5 prompts per scenario.
