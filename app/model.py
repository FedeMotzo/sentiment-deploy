"""
model.py — Caricamento e inferenza del modello di Sentiment Analysis

Responsabilità:
- Caricare il pipeline sklearn da file .pkl
- Esporre una funzione di predizione che restituisce sentiment + confidence
"""

import pickle
import numpy as np
from pathlib import Path


# Percorso del modello relativo a questo file
MODEL_PATH = Path(__file__).parent / "model.pkl"

# Variabile globale — il modello viene caricato una volta sola all'avvio
_pipeline = None


def load_model():
    """
    Carica il pipeline sklearn dal file .pkl.
    Viene chiamata una volta sola all'avvio dell'API.
    Solleva un errore esplicito se il file non viene trovato.
    """
    global _pipeline

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modello non trovato in {MODEL_PATH}. "
        )

    with open(MODEL_PATH, "rb") as f:
        _pipeline = pickle.load(f)

    print(f"✅ Modello caricato da {MODEL_PATH}")


def predict(text: str) -> dict:
    """
    Esegue la predizione su una singola stringa di testo.

    Args:
        text: La recensione da classificare.

    Returns:
        dict con:
          - sentiment: "positive" | "negative" | "neutral"
          - confidence: probabilità della classe predetta (0.0 - 1.0)
          - probabilities: dizionario con le probabilità di tutte le classi

    Raises:
        RuntimeError: se il modello non è stato caricato.
    """
    if _pipeline is None:
        raise RuntimeError("Modello non caricato. Chiamare load_model() prima.")

    # La pipeline si aspetta una lista di stringhe
    probas = _pipeline.predict_proba([text])[0]
    classes = _pipeline.classes_

    # Indice della classe con probabilità più alta
    predicted_idx = int(np.argmax(probas))
    predicted_class = classes[predicted_idx]
    confidence = float(probas[predicted_idx])

    return {
        "sentiment": predicted_class,
        "confidence": round(confidence, 4),
        "probabilities": {
            cls: round(float(prob), 4)
            for cls, prob in zip(classes, probas)
        }
    }