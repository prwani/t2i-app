# Asset Creation Workflow Web

Modern Next.js/React/TypeScript frontend for the Asset Creation Workflow.

Run the FastAPI backend first from the repository root:

```bash
uvicorn api.main:app --reload --port 8000
```

Then start the frontend:

```bash
npm install
npm run dev
```

The API client uses `NEXT_PUBLIC_API_BASE_URL` and defaults to `http://localhost:8000`.

See [../docs/web-app.md](../docs/web-app.md) for full setup.
