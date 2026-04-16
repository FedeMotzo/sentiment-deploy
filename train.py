"""
train.py — Addestramento del modello di Sentiment Analysis
Pipeline: TF-IDF + Logistic Regression
Dataset: Yelp Review Full Hugging Face datasets
  - label 0-1 (1-2 stelle) → negative
  - label 2   (3 stelle)   → neutral
  - label 3-4 (4-5 stelle) → positive
Output: app/model.pkl
"""

import pickle
import numpy as np
from datasets import load_dataset
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split


# ─── 1. LABEL MAPPING ────────────────────────────────────────────────────────

def rating_to_sentiment(rating: int) -> str:
    """
    Converte il rating in stelle in un'etichetta di sentimento.
    Il dataset yelp_review_full usa label 0-4 (corrispondenti a 1-5 stelle).
      0-1 (1-2 stelle) → negative
      2   (3 stelle)   → neutral
      3-4 (4-5 stelle) → positive
    """
    if rating <= 1:
        return "negative"
    elif rating == 2:
        return "neutral"
    else:
        return "positive"


# ─── 2. CARICAMENTO DATASET ──────────────────────────────────────────────────

def load_data(max_samples: int = 90_000):
    """
    Carica il dataset Yelp Review Full da Hugging Face.
    Contiene recensioni con 1-5 stelle.
    Campionamento bilanciato: max_samples/3 esempi per classe.
    """
    print("Caricamento dataset...")
    dataset = load_dataset("yelp_review_full", split="train")

    per_class = max_samples // 3
    counts = {"negative": 0, "neutral": 0, "positive": 0}
    texts, labels = [], []

    print(f"Campionamento {max_samples} esempi bilanciati ({per_class} per classe)...")
    for example in dataset:
        text = example["text"].strip()
        label = rating_to_sentiment(example["label"])

        if not text:
            continue

        if counts[label] < per_class:
            texts.append(text)
            labels.append(label)
            counts[label] += 1

        if all(v >= per_class for v in counts.values()):
            break

    print(f"Distribuzione classi: {counts}")
    return texts, labels


# ─── 3. TRAINING ─────────────────────────────────────────────────────────────

def train_model(texts: list, labels: list):
    """
    Pipeline TF-IDF + Logistic Regression.

    TfidfVectorizer:
      - max_features=50000: vocabolario limitato per contenere la dimensionalità
      - ngram_range=(1,2): unigrammi e bigrammi per catturare frasi come "not good"
      - sublinear_tf=True: scala logaritmica delle frequenze
      - min_df=2: ignora termini che appaiono in meno di 2 documenti

    LogisticRegression:
      - C=1.0: regolarizzazione L2 di default
      - max_iter=1000: sufficiente per convergere su dataset grandi
      - class_weight='balanced': compensa eventuali squilibri tra le classi
    """
    print("\nSplit train/test (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels,
        test_size=0.2,
        random_state=42,
        stratify=labels
    )

    print(f"Train: {len(X_train)} esempi | Test: {len(X_test)} esempi")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=50_000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            strip_accents="unicode",
            analyzer="word",
            token_pattern=r"\b[a-zA-Z][a-zA-Z]+\b",
        )),
        ("clf", LogisticRegression(
            C=1.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ])

    print("\nTraining in corso...")
    pipeline.fit(X_train, y_train)

    # ─── 4. VALUTAZIONE ──────────────────────────────────────────────────────
    print("\nValutazione sul test set:")
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"   Accuracy: {acc:.4f} ({acc*100:.2f}%)")
    print("\n" + classification_report(
        y_test, y_pred,
        target_names=["negative", "neutral", "positive"]
    ))

    return pipeline, X_test, y_test


# ─── 5. SERIALIZZAZIONE ──────────────────────────────────────────────────────

def save_model(pipeline: Pipeline, path: str = "app/model.pkl"):
    with open(path, "wb") as f:
        pickle.dump(pipeline, f)
    print(f"\nModello salvato in: {path}")


# ─── 6. SMOKE TEST ───────────────────────────────────────────────────────────

def smoke_test(pipeline: Pipeline):
    """Verifica rapida che il modello funzioni correttamente dopo il training."""
    examples = [
        ("positive", "This product is absolutely amazing! Best purchase ever."),
        ("negative", "Terrible quality, broke after one day. Total waste of money."),
        ("neutral",  "It's okay, nothing special. Does the job I guess."),
    ]
    print("\nSmoke test:")
    texts = [e[1] for e in examples]
    predictions = pipeline.predict(texts)
    probas = pipeline.predict_proba(texts)

    all_passed = True
    for (expected, text), pred, proba in zip(examples, predictions, probas):
        confidence = float(np.max(proba))
        status = "OK" if pred == expected else "WARNING"
        if pred != expected:
            all_passed = False
        print(f"   {status} [{pred.upper():8s}] ({confidence:.2f}) → \"{text[:60]}\"")

    if all_passed:
        print("\n✅ Tutti i test smoke superati!")
    else:
        print("\n⚠️  Alcuni esempi non corrispondono all'atteso (normale per casi borderline).")


# ─── MAIN ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    texts, labels = load_data(max_samples=90_000)
    pipeline, X_test, y_test = train_model(texts, labels)
    smoke_test(pipeline)
    save_model(pipeline, path="app/model.pkl")
    print("\nTraining completato.")