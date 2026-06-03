# Web and API app

The preferred local user experience is a Next.js frontend in `web/` backed by a FastAPI service in `api/`. Both reuse the shared `t2i_core` SDK and the existing app service layer for image generation, prompt improvement, evaluation, comparison, and ranking.

## Local setup

From the repository root:

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e "packages/t2i_core[dev,api]"
cp .env.example .env
az login
```

Fill `.env` with endpoint and deployment variable names from `.env.example`. Do not commit secrets.

## Run the backend

```bash
uvicorn api.main:app --reload --port 8000
```

Useful endpoints:

- `GET /health`
- `GET /api/scenarios`
- `POST /api/prompts/improve`
- `POST /api/generations`
- `GET /api/generations/{job_id}`
- `POST /api/evaluations`
- `POST /api/comparisons`

Generated assets are served locally from `/assets/generated`. This is local, stateless storage and should be replaced with durable storage for multi-user production use.

## Run the frontend

In a second terminal:

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend uses `NEXT_PUBLIC_API_BASE_URL` and defaults to `http://localhost:8000`.

## Related docs

- [Architecture](architecture.md)
- [Image scenarios](scenarios.md)
- [Evaluation pipeline](evaluation.md)
