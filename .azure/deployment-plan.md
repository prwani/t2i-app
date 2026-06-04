# Deployment Plan

Status: Validated

## Goal

Add, test, verify, and document Azure deployment for the Next.js frontend in addition to the already-tested FastAPI backend deployment.

## Scope

- Analyze the existing Next.js frontend deployment needs.
- Add frontend Azure deployment artifacts and documentation.
- Test deployed frontend-to-backend connectivity.
- Correct any docs or code issues found during deployment testing.

## Proposed Architecture

- Keep the existing tested FastAPI backend Container App (`t2i-app`) on port 8000.
- Add a separate Next.js frontend Container App (`t2i-web`) on port 3000 in the same Container Apps environment.
- Build/push frontend image to the existing ACR using a unique tag.
- Configure the frontend with `NEXT_PUBLIC_API_BASE_URL=https://<backend-fqdn>`.
- Update backend CORS to support configured deployed frontend origins instead of localhost-only origins.
- Document both backend and frontend deployment paths, including smoke tests.

## Execution Steps

1. Add `web/Dockerfile` for production Next.js on Azure Container Apps.
2. Add a frontend health route or equivalent lightweight verification endpoint.
3. Update backend CORS to read allowed origins from environment variables while preserving localhost defaults.
4. Update Azure deployment docs/blog with frontend Container App deployment, `NEXT_PUBLIC_API_BASE_URL`, CORS, unique image tags, and smoke tests.
5. Build and locally validate the web app.
6. Build frontend image in ACR.
7. Deploy frontend Container App to the existing Azure Container Apps environment.
8. Update backend Container App CORS env var with the deployed frontend origin.
9. Verify frontend deployment by loading the frontend and confirming it can call backend scenario metadata.
10. Correct any failed steps in docs/code and retest.

## Validation

- Python tests pass.
- Next.js lint/build pass.
- Backend health and scenario APIs pass after CORS update.
- Frontend Container App health/page load passes.
- Frontend-to-backend API call succeeds from deployed frontend.

## Section 7: Validation Proof

- 2026-06-04T14:09+05:30: `cd web && npm run lint && npm run build` passed for the updated Next.js frontend.
- 2026-06-04T14:10+05:30: `az account show` confirmed subscription `ME-M365CPI88726844-prafullawani-1` (`6f52fedd-df2c-47f7-a01f-e48682864606`), confirmed by user for redeployment.
- 2026-06-04T14:10+05:30: `az acr show -g generative_media -n t2iapp6f52fedd` returned provisioning state `Succeeded`.
- 2026-06-04T14:10+05:30: `az containerapp show -g generative_media -n t2i-web` returned provisioning state `Succeeded` and current frontend FQDN.
- 2026-06-04T14:10+05:30: `az containerapp show -g generative_media -n t2i-app` returned provisioning state `Succeeded` and backend FQDN.
- 2026-06-04T14:23+05:30: `cd web && npm run lint && npm run build` passed for the frontend generation progress update.
- 2026-06-04T14:26+05:30: `cd web && npm run lint && npm run build` passed after preserving parallel one-request-per-model generation while showing per-model progress.
- 2026-06-04T14:51+05:30: `cd web && npm run lint && npm run build` passed after adding auto-collapse/expand behavior to the generation progress panel.
- 2026-06-04T15:03+05:30: `cd web && npm run lint && npm run build` passed after moving sample input previews into the main prompt workspace.
- 2026-06-04T15:04+05:30: `cd web && npm run lint && npm run build` passed after converting sample input previews to compact clickable thumbnails.
- 2026-06-04T15:18+05:30: `PYTHONPATH=packages/t2i_core/src:. .venv/bin/python -m pytest -q packages/t2i_core/tests` passed (`41 passed`) after adding server-side `sample_path` asset references.
- 2026-06-04T15:18+05:30: `cd web && npm run lint && npm run build` passed after changing sample inputs to send lightweight `sample_path` references instead of base64 image data.
- 2026-06-04T15:44+05:30: `cd web && npm run lint && npm run build` passed after changing the progress label to include the expected 5-10 minute wait time.
- 2026-06-04T15:59+05:30: `PYTHONPATH=packages/t2i_core/src:. .venv/bin/python -m pytest -q packages/t2i_core/tests` passed (`41 passed`) after making generation jobs return immediately and complete in the background.
- 2026-06-04T15:59+05:30: `cd web && npm run lint && npm run build` passed after updating generation polling for multiple job IDs and replacing the 3-scenario initial fallback with a loading state.
- 2026-06-04T10:37Z: Live deployment verification passed after async generation rollout: backend `/health`, frontend `/health`, scenario API count (`8`), studio page load (`200`), frontend JS bundle markers (`Generation progress (This may take 5-10 mins)`, `sample_path`), and invalid `sample_path` async failure path (`Unknown sample asset: missing-file.png`).

## Results

- Backend URL: `https://t2i-app.bravepond-67417fc2.swedencentral.azurecontainerapps.io`
- Frontend URL: `https://t2i-web.bravepond-67417fc2.swedencentral.azurecontainerapps.io`
- Verified backend health, frontend health, scenario API, frontend page content, embedded backend URL, and CORS preflight from the deployed frontend origin.
- 2026-06-04: Rebuilt and redeployed frontend image `t2iapp6f52fedd.azurecr.io/t2i-web:web-20260604141437` to revision `t2i-web--web-20260604141437`; verified frontend health, backend health, scenario page load, embedded backend URL, multi-model UI strings, and evaluation progress/ready UI strings.
- 2026-06-04: Rebuilt and redeployed frontend image `t2iapp6f52fedd.azurecr.io/t2i-web:web-20260604142636` to revision `t2i-web--web-20260604142636`; verified frontend health, backend health, scenario page load, embedded backend URL, and optimized per-model generation progress UI strings.
- 2026-06-04: Rebuilt and redeployed frontend image `t2iapp6f52fedd.azurecr.io/t2i-web:web-20260604145246` to revision `t2i-web--web-20260604145246`; verified frontend health, backend health, scenario page load, embedded backend URL, and auto-collapse/expand generation progress UI strings.
- 2026-06-04: Rebuilt and redeployed frontend image `t2iapp6f52fedd.azurecr.io/t2i-web:web-20260604150658` to revision `t2i-web--web-20260604150658`; verified frontend health, backend health, multi-image composition page load, embedded backend URL, compact sample thumbnail panel, clickable sample thumbnail labels, and existing full-size lightbox strings.
- 2026-06-04: Rebuilt and redeployed backend image `t2iapp6f52fedd.azurecr.io/t2i-app:api-20260604151756` to revision `t2i-app--api-20260604151756`; verified backend health and no-generation `sample_path` validation.
- 2026-06-04: Rebuilt and redeployed frontend image `t2iapp6f52fedd.azurecr.io/t2i-web:web-20260604151945` to revision `t2i-web--web-20260604151945`; verified frontend health, multi-image composition page load, backend URL wiring, `sample_path` bundle marker, removed browser-side sample download error path, and compact clickable sample thumbnail strings.
- 2026-06-04: Rebuilt and redeployed frontend image `t2iapp6f52fedd.azurecr.io/t2i-web:web-20260604154412` to revision `t2i-web--web-20260604154412`; verified frontend health, backend health, active revision image, and deployed bundle marker `Generation progress (This may take 5-10 mins)`.
- 2026-06-04: Rebuilt and redeployed backend image `t2iapp6f52fedd.azurecr.io/t2i-app:api-20260604160032` to revision `t2i-app--api-20260604160032`; verified async `/api/generations` returns `queued` immediately and jobs transition independently.
- 2026-06-04: Rebuilt and redeployed frontend image `t2iapp6f52fedd.azurecr.io/t2i-web:web-20260604160221` to revision `t2i-web--web-20260604160221`; verified frontend health, multi-image composition page load, loading-state/progress/sample-path bundle markers, and backend URL wiring.
