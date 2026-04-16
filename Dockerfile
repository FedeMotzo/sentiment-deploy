# ─── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copiamo le dipendenze installate nello stage builder
COPY --from=builder /install /usr/local

# Copiamo il codice dell'applicazione
COPY app/ ./app/

# Porta esposta dall'API
EXPOSE 8000

# Healthcheck: Docker verifica ogni 30s che l'API risponda
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Comando di avvio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]