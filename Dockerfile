FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml README.md ./
COPY api api
COPY app app
COPY packages packages
COPY skills skills

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e "packages/t2i_core[api]"

RUN mkdir -p api/generated_assets \
    && chown -R app:app /app

USER app
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
