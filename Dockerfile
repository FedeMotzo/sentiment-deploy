# ─── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Utente non-root
RUN groupadd -r app && useradd -r -g app -d /app app

# Dipendenze dallo stage builder
COPY --from=builder /install /usr/local

COPY --chown=app:app app/ ./app/

# Guard: fail-fast se il modello non è stato copiato nell'immagine
RUN test -f ./app/model.pkl || { \
        echo "ERROR: app/model.pkl non trovato nel build context."; \
        echo "Esegui 'python scripts/train.py' prima di 'docker build'."; \
        exit 1; \
    }

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]