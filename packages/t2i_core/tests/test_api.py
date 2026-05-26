from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from api.main import app
from app.services import GeneratedAsset
from t2i_core.types import GenerationResult


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scenarios_include_frontend_metadata() -> None:
    response = client.get("/api/scenarios")

    assert response.status_code == 200
    scenarios = response.json()
    assert {scenario["id"] for scenario in scenarios} >= {"text-to-image", "inpainting"}
    text_to_image = next(scenario for scenario in scenarios if scenario["id"] == "text-to-image")
    assert text_to_image["default_model"] == "MAI-Image-2e"
    assert text_to_image["forced_model"] is None
    assert text_to_image["example_prompts"]


def test_generation_returns_async_ready_job_shape(monkeypatch) -> None:
    async def fake_generate_images(prompt: str, model: str, *, size: str, quality: str, n: int):
        return [
            GeneratedAsset(
                name="example.png",
                result=GenerationResult(
                    image=b"image-bytes",
                    prompt=prompt,
                    model=model,
                    size=size,
                    quality=quality,
                ),
            )
        ]

    monkeypatch.setattr("api.main.services.generate_images", fake_generate_images)

    response = client.post(
        "/api/generations",
        json={"scenario": "text-to-image", "prompt": "A clean product hero image"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"]
    assert payload["status"] == "succeeded"
    assert payload["error"] is None
    assert payload["assets"][0]["url"].startswith("/assets/generated/")


def test_evaluation_accepts_external_base64_asset(monkeypatch) -> None:
    async def fake_evaluate_image(image: bytes, prompt: str, layers: list[str], **kwargs):
        assert image == b"image-bytes"
        assert prompt == "A prompt"
        return {
            "prompt": prompt,
            "layers_run": layers,
            "composite_score": 0.9,
        }

    monkeypatch.setattr("api.main.services.evaluate_image", fake_evaluate_image)
    encoded = base64.b64encode(b"image-bytes").decode("ascii")

    response = client.post(
        "/api/evaluations",
        json={"prompt": "A prompt", "assets": [{"data": encoded, "name": "external.png"}]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["reports"][0]["name"] == "external.png"
