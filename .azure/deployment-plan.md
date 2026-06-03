# Deployment Plan

Status: Complete

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

## Results

- Backend URL: `https://t2i-app.bravepond-67417fc2.swedencentral.azurecontainerapps.io`
- Frontend URL: `https://t2i-web.bravepond-67417fc2.swedencentral.azurecontainerapps.io`
- Verified backend health, frontend health, scenario API, frontend page content, embedded backend URL, and CORS preflight from the deployed frontend origin.
