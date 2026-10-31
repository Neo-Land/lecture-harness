# Default target is the read-only public demo, so a plain build can never publish the full app.
# The full app, for your own machine only, is `--target api`.
FROM python:3.13-slim AS base
WORKDIR /app
ENV PYTHONUNBUFFERED=1 HARNESS_DATA_DIR=/app/data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY evals evals
COPY scripts scripts
RUN mkdir -p data && chown 1000 data
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.api:app --host 0.0.0.0 --port $PORT --proxy-headers"]

FROM base AS api
# LibreOffice converts PPTX slides to images
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*
ENV HOME=/tmp
USER 1000

FROM base AS demo
ENV HARNESS_OFFLINE=true HARNESS_DEMO=true
# The source PDFs are deleted so the image holds only text and license-cleared slide images
RUN python scripts/seed_demo.py && rm -rf evals/decks data/files && chown -R 1000 data
USER 1000
