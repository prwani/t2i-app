FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8000 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml README.md ./
COPY .streamlit .streamlit
COPY app app
COPY packages packages
COPY skills skills

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e "packages/t2i_core[app]"

USER app
EXPOSE 8000

CMD ["streamlit", "run", "app/Home.py", "--server.address=0.0.0.0"]
