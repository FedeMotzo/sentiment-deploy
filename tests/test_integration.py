"""
test_integration.py — Integration test sugli endpoint FastAPI

Testano l'intera stack HTTP: request → validazione → modello → response.
Usano TestClient di FastAPI che simula richieste HTTP senza avviare un server reale.
"""

import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Client di test che gestisce il lifespan dell'app e carica il modello"""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self, client):
        response = client.get("/health")
        assert response.json() == {"status": "ok"}


class TestPredictEndpoint:

    def test_predict_positive(self, client):
        response = client.post("/predict", json={
            "review": "This product is absolutely amazing! Best purchase ever."
        })
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "positive"
        assert data["confidence"] > 0.5

    def test_predict_negative(self, client):
        response = client.post("/predict", json={
            "review": "Terrible quality, broke after one day. Total waste of money."
        })
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "negative"

    def test_predict_response_structure(self, client):
        """Verifica che la response abbia sempre tutti i campi."""
        response = client.post("/predict", json={"review": "Good product."})
        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        assert "confidence" in data
        assert "probabilities" in data

    def test_predict_empty_review_returns_422(self, client):
        """Una review vuota deve restituire 422 Unprocessable Entity."""
        response = client.post("/predict", json={"review": ""})
        assert response.status_code == 422

    def test_predict_missing_field_returns_422(self, client):
        """Body senza il campo 'review' deve restituire 422."""
        response = client.post("/predict", json={"text": "something"})
        assert response.status_code == 422

    def test_predict_short_review_returns_422(self, client):
        """Una review troppo corta deve restituire 422."""
        response = client.post("/predict", json={"review": "ok"})
        assert response.status_code == 422

    def test_predict_confidence_range(self, client):
        """La confidence deve essere sempre tra 0 e 1."""
        response = client.post("/predict", json={"review": "Great value for money!"})
        data = response.json()
        assert 0.0 <= data["confidence"] <= 1.0

    def test_predict_probabilities_sum(self, client):
        """Le probabilità devono sommare a 1."""
        response = client.post("/predict", json={"review": "Really happy with this."})
        data = response.json()
        total = sum(data["probabilities"].values())
        assert abs(total - 1.0) < 1e-4


class TestMetricsEndpoint:

    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        """Prometheus si aspetta text/plain."""
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_contains_prediction_counter(self, client):
        """Dopo una predizione, il counter deve apparire nelle metriche."""
        client.post("/predict", json={"review": "Amazing product!"})
        response = client.get("/metrics")
        assert "sentiment_predictions_total" in response.text

    def test_metrics_contains_latency_histogram(self, client):
        response = client.get("/metrics")
        assert "sentiment_prediction_latency_seconds" in response.text