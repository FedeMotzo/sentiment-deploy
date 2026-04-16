"""
test_unit.py — Unit test sul modello di inferenza

Testano la funzione predict() in isolamento,
senza avviare il server FastAPI.
"""

import pytest
import sys
import os

# Aggiungiamo la root del progetto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.model import load_model, predict


@pytest.fixture(scope="module", autouse=True)
def setup_model():
    """Carica il modello una volta per tutti i test del modulo."""
    load_model()


class TestPredict:

    def test_positive_review(self):
        result = predict("This product is absolutely amazing! Best purchase ever.")
        assert result["sentiment"] == "positive"
        assert result["confidence"] > 0.5
        assert "probabilities" in result

    def test_negative_review(self):
        result = predict("Terrible quality, broke after one day. Total waste of money.")
        assert result["sentiment"] == "negative"
        assert result["confidence"] > 0.5

    def test_neutral_review(self):
        result = predict("It is okay, nothing special. Does the job.")
        assert result["sentiment"] in ["positive", "negative", "neutral"]
        # Il neutral è ambiguo — verifichiamo solo che la struttura sia corretta

    def test_response_structure(self):
        """Verifica che la risposta abbia sempre tutti i campi attesi."""
        result = predict("Good product.")
        assert "sentiment" in result
        assert "confidence" in result
        assert "probabilities" in result

    def test_sentiment_values(self):
        """Il sentiment deve essere sempre una delle tre classi valide."""
        result = predict("Some random review text here.")
        assert result["sentiment"] in ["positive", "negative", "neutral"]

    def test_confidence_range(self):
        """La confidence deve essere sempre tra 0 e 1."""
        result = predict("Great value for money!")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_probabilities_sum_to_one(self):
        """Le probabilità delle tre classi devono sommare a 1."""
        result = predict("Really happy with this purchase.")
        total = sum(result["probabilities"].values())
        assert abs(total - 1.0) < 1e-4  # tolleranza floating point

    def test_probabilities_keys(self):
        """Le probabilità devono contenere tutte e tre le classi."""
        result = predict("This is a test review.")
        assert set(result["probabilities"].keys()) == {"positive", "negative", "neutral"}