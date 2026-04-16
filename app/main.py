"""
main.py — API REST per il modello di Sentiment Analysis

Endpoint:
  POST /predict  → classifica una recensione
  GET  /metrics  → espone metriche per Prometheus
  GET  /health   → healthcheck per Docker e Jenkins
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, field_validator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.model import load_model, predict
from app.metrics import (
    PREDICTIONS_TOTAL,
    PREDICTION_ERRORS_TOTAL,
    PREDICTION_LATENCY,
    update_system_metrics,
)


# ─── LIFESPAN ────────────────────────────────────────────────────────────────
# Il lifespan gestisce le operazioni di startup e shutdown dell'app.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # carica il modello una volta sola all'avvio
    load_model()
    yield


# ─── APP ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sentiment Analysis API",
    description="Classifica recensioni e-commerce in positive, negative, neutral.",
    version="1.0.0",
    lifespan=lifespan,
)


# ─── SCHEMA INPUT/OUTPUT ─────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    review: str

    @field_validator("review")
    @classmethod
    def review_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Il campo 'review' non può essere vuoto.")
        if len(v) < 3:
            raise ValueError("La recensione è troppo corta per essere classificata.")
        return v


class PredictionResponse(BaseModel):
    sentiment: str
    confidence: float
    probabilities: dict[str, float]


# ─── ENDPOINT /predict ───────────────────────────────────────────────────────

@app.post("/predict", response_model=PredictionResponse)
async def predict_sentiment(request: ReviewRequest):
    """
    Classifica il sentiment di una recensione.

    Body JSON:
        { "review": "This product is amazing!" }

    Response:
        {
            "sentiment": "positive",
            "confidence": 0.96,
            "probabilities": {
                "negative": 0.02,
                "neutral": 0.02,
                "positive": 0.96
            }
        }
    """
    start_time = time.time()

    try:
        result = predict(request.review)

        # Aggiorna metriche
        PREDICTIONS_TOTAL.labels(sentiment=result["sentiment"]).inc()
        PREDICTION_LATENCY.observe(time.time() - start_time)

        return result

    except Exception as e:
        PREDICTION_ERRORS_TOTAL.inc()
        raise HTTPException(status_code=500, detail=str(e))


# ─── ENDPOINT /metrics ───────────────────────────────────────────────────────

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Espone le metriche in formato Prometheusì.
    """
    update_system_metrics()
    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ─── ENDPOINT /health ────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """
    Healthcheck per Jenkins.
    Restituisce 200 se l'API è attiva e il modello è caricato.
    """
    return {"status": "ok"}