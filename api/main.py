"""FastAPI backend exposing T2I generation and evaluation workflows."""

from __future__ import annotations

import base64
import binascii
import os
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.catalog import SCENARIOS, get_scenario
from api.schemas import (
    AssetInput,
    AssetResponse,
    ComparisonResponse,
    EvaluationReportResponse,
    EvaluationRequest,
    EvaluationResponse,
    GenerationJobResponse,
    GenerationRequest,
    ImprovePromptRequest,
    ImprovePromptResponse,
    LayerName,
    ScenarioResponse,
)
from app import services
from app.services import GeneratedAsset


GENERATED_DIR = Path(os.environ.get("GENERATED_ASSETS_DIR", "/tmp/t2i-generated-assets"))
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_ASSETS_DIR = Path(__file__).resolve().parent.parent / "app" / "sample_assets"
LOCAL_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]


def _cors_origins() -> list[str]:
    configured = [
        origin.strip().rstrip("/")
        for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    return [*LOCAL_CORS_ORIGINS, *configured]


app = FastAPI(title="T2I Backend API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/assets/generated", StaticFiles(directory=GENERATED_DIR), name="generated-assets")
app.mount("/assets/samples", StaticFiles(directory=SAMPLE_ASSETS_DIR), name="sample-assets")

GENERATION_JOBS: dict[str, GenerationJobResponse] = {}
EVALUATION_JOBS: dict[str, EvaluationResponse] = {}
ASSET_STORE: dict[str, tuple[bytes, AssetResponse]] = {}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/scenarios", response_model=list[ScenarioResponse])
async def scenarios() -> list[ScenarioResponse]:
    return [
        ScenarioResponse(
            id=item["id"],
            label=item["label"],
            default_model=item["default_model"],
            forced_model=item["forced_model"],
            model_options=item["model_options"],
            example_prompts=item["example_prompts"],
            example_extras=item.get("example_extras", []),
            recommended_eval_layers=item["recommended_eval_layers"],  # type: ignore[arg-type]
            evaluation_recommended=item["evaluation_recommended"],
            compare_recommended=item["compare_recommended"],
        )
        for item in SCENARIOS.values()
    ]


@app.post("/api/prompts/improve", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest) -> ImprovePromptResponse:
    scenario = _scenario_or_404(request.scenario)
    try:
        prompt = await services.improve_prompt_with_ai(request.prompt, scenario["service_label"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Prompt improvement failed: {exc}") from exc
    return ImprovePromptResponse(prompt=prompt)


@app.post("/api/generations", response_model=GenerationJobResponse)
async def create_generation(request: GenerationRequest, background_tasks: BackgroundTasks) -> GenerationJobResponse:
    job_id = uuid4().hex
    job = GenerationJobResponse(job_id=job_id, status="queued")
    GENERATION_JOBS[job_id] = job
    background_tasks.add_task(_complete_generation_job, job_id, request)
    return job


async def _complete_generation_job(job_id: str, request: GenerationRequest) -> None:
    job = GENERATION_JOBS[job_id]
    job.status = "running"
    try:
        assets = await _run_generation(request)
        if request.evaluate:
            layers = request.layers or _scenario_layers(request.scenario)
            assets = await services.evaluate_generated_assets(
                assets,
                layers,  # type: ignore[arg-type]
            )
        job.assets = [
            _persist_asset(job_id, index, asset)
            for index, asset in enumerate(assets, start=1)
        ]
        job.status = "succeeded"
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)


@app.get("/api/generations/{job_id}", response_model=GenerationJobResponse)
async def get_generation(job_id: str) -> GenerationJobResponse:
    try:
        return GENERATION_JOBS[job_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Generation job not found") from exc


@app.post("/api/evaluations", response_model=EvaluationResponse)
async def create_evaluation(request: EvaluationRequest) -> EvaluationResponse:
    job_id = uuid4().hex
    response = EvaluationResponse(job_id=job_id, status="running")
    EVALUATION_JOBS[job_id] = response
    try:
        response.reports = await _evaluate_assets(request.assets, request.prompt, request.layers)
        response.status = "succeeded"
    except Exception as exc:
        response.status = "failed"
        response.error = str(exc)
    return response


@app.post("/api/comparisons", response_model=ComparisonResponse)
async def create_comparison(request: EvaluationRequest) -> ComparisonResponse:
    job_id = uuid4().hex
    response = ComparisonResponse(job_id=job_id, status="running")
    EVALUATION_JOBS[job_id] = response
    try:
        reports = await _evaluate_assets(request.assets, request.prompt, request.layers)
        response.reports = reports
        response.ranked = sorted(
            reports,
            key=lambda item: item.report.get("composite_score", 0.0),
            reverse=True,
        )
        response.status = "succeeded"
    except Exception as exc:
        response.status = "failed"
        response.error = str(exc)
    return response


async def _run_generation(request: GenerationRequest) -> list[GeneratedAsset]:
    scenario = _scenario_or_404(request.scenario)
    model = scenario["forced_model"] or request.model or scenario["default_model"]
    service_label = scenario["service_label"]
    if service_label == "Text-to-image generation":
        return await services.generate_images(
            request.prompt,
            model,  # type: ignore[arg-type]
            size=request.size,
            quality=request.quality,
            n=request.n,
        )
    if service_label == "Brand template":
        brand_colors = request.brand_colors or ["#0078D4", "#FFFFFF"]
        font_style = request.font_style or "modern sans-serif"
        tone = request.tone or "confident"
        return await services.generate_brand_template_assets(
            request.prompt,
            model,  # type: ignore[arg-type]
            colors=brand_colors,
            font_style=font_style,
            tone=tone,
            logo_description=request.logo_description,
            size=request.size,
            quality=request.quality,
            n=request.n,
        )
    if service_label == "Text rendering":
        text = request.text or "LAUNCH DAY\nJOIN THE WAITLIST"
        return await services.generate_text_rendering_assets(
            request.prompt,
            model,  # type: ignore[arg-type]
            text=text,
            size=request.size,
            quality=request.quality,
            n=request.n,
        )
    if service_label == "Aspect-ratio package":
        formats = request.formats or ["instagram_square", "linkedin_banner", "desktop_hero"]
        return await services.generate_aspect_package(
            request.prompt,
            model,  # type: ignore[arg-type]
            formats,
            quality=request.quality,
        )
    if service_label == "Multi-image composition":
        images = [_asset_bytes(asset) for asset in request.source_images]
        if not 2 <= len(images) <= 16:
            raise ValueError("multi-image composition requires 2 to 16 source_images")
        return await services.compose_uploaded_images(
            images,
            request.prompt,
            model,  # type: ignore[arg-type]
            size=request.size,
            quality=request.quality,
        )
    if service_label == "Inpainting":
        if len(request.source_images) != 1:
            raise ValueError("inpainting requires exactly one source image")
        return await services.inpaint_uploaded_image(
            _asset_bytes(request.source_images[0]),
            request.prompt,
            model,  # type: ignore[arg-type]
            mask=_asset_bytes(request.mask) if request.mask else None,
            size=request.size,
            quality=request.quality,
        )
    if service_label == "Product placement":
        environments = request.environments or [
            "on a marble kitchen counter",
            "inside a premium retail display",
            "on a sunny outdoor patio",
        ]
        if len(request.source_images) != 1:
            raise ValueError("product placement requires one source image and environments")
        return await services.place_product_assets(
            _asset_bytes(request.source_images[0]),
            environments,
            model,  # type: ignore[arg-type]
            size=request.size,
            quality=request.quality,
        )
    if service_label == "Multi-turn refinement":
        refinements = request.refinements or [
            "Make the lighting more dramatic",
            "Add a subtle reflection on the floor",
            "Make the background darker",
        ]
        return await services.refine_image_assets(
            request.prompt,
            refinements,
            model,  # type: ignore[arg-type]
            size=request.size,
            quality=request.quality,
        )
    raise ValueError(f"Unsupported scenario: {request.scenario}")


async def _evaluate_assets(
    assets: list[AssetInput],
    prompt: str,
    layers: list[LayerName],
) -> list[EvaluationReportResponse]:
    reports: list[EvaluationReportResponse] = []
    for asset in assets:
        image, stored = _asset_bytes_with_metadata(asset)
        report = await services.evaluate_image(
            image,
            asset.prompt or prompt,
            layers,
            model_used=asset.model or (stored.model if stored else None),
            image_path=asset.name or (stored.name if stored else None),
        )
        reports.append(
            EvaluationReportResponse(
                asset_id=asset.id,
                name=asset.name or (stored.name if stored else None),
                report=_model_dump(report),
            )
        )
    return reports


def _persist_asset(job_id: str, index: int, asset: GeneratedAsset) -> AssetResponse:
    safe_name = _safe_filename(asset.name or f"asset-{index}.png")
    name = f"{job_id}-{index}-{safe_name}"
    path = GENERATED_DIR / name
    path.write_bytes(asset.result.image)
    asset_id = f"{job_id}:{index}"
    response = AssetResponse(
        id=asset_id,
        name=asset.name,
        url=f"/assets/generated/{name}",
        prompt=asset.result.prompt,
        revised_prompt=asset.result.revised_prompt,
        model=asset.result.model,
        size=asset.result.size,
        quality=asset.result.quality,
        caption=asset.caption,
        evaluation=_model_dump(asset.evaluation) if asset.evaluation else None,
    )
    ASSET_STORE[asset_id] = (asset.result.image, response)
    return response


def _asset_bytes(asset: AssetInput | None) -> bytes:
    if asset is None:
        raise ValueError("asset is required")
    image, _ = _asset_bytes_with_metadata(asset)
    return image


def _asset_bytes_with_metadata(asset: AssetInput) -> tuple[bytes, AssetResponse | None]:
    if asset.id:
        stored = ASSET_STORE.get(asset.id)
        if stored:
            return stored
        # Fallback: try to read from generated assets directory (survives server restarts)
        if ":" in asset.id:
            job_id, idx = asset.id.rsplit(":", 1)
            prefix = f"{job_id}-{idx}-"
            for path in GENERATED_DIR.iterdir():
                if path.name.startswith(prefix) and path.is_file():
                    return path.read_bytes(), None
        raise ValueError(f"Unknown asset id: {asset.id}")
    if asset.sample_path:
        sample_path = (SAMPLE_ASSETS_DIR / asset.sample_path).resolve()
        sample_root = SAMPLE_ASSETS_DIR.resolve()
        if sample_root not in sample_path.parents or not sample_path.is_file():
            raise ValueError(f"Unknown sample asset: {asset.sample_path}")
        return sample_path.read_bytes(), None
    if not asset.data:
        raise ValueError("asset data, id, or sample_path is required")
    data = asset.data.split(",", 1)[1] if asset.data.startswith("data:") else asset.data
    try:
        return base64.b64decode(data, validate=True), None
    except (binascii.Error, ValueError) as exc:
        raise ValueError("asset data must be valid base64") from exc


def _scenario_or_404(scenario_id: str):
    try:
        return get_scenario(scenario_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scenario_layers(scenario_id: str) -> list[LayerName]:
    return _scenario_or_404(scenario_id)["recommended_eval_layers"]  # type: ignore[return-value]


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    raise TypeError(f"Unsupported response payload: {type(value).__name__}")


def _safe_filename(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(name).name).strip(".-")
    return sanitized or "asset.png"
