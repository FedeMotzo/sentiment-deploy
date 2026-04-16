# Step 1 — Training del modello di Sentiment Analysis

## Obiettivo

Addestrare un modello di Sentiment Analysis in grado di classificare recensioni e-commerce in tre categorie: **positive**, **negative**, **neutral**. Il modello viene serializzato in formato `.pkl` per essere servito tramite API REST.

---

## Dataset

**Yelp Review Full** — disponibile pubblicamente su [Hugging Face Hub](https://huggingface.co/datasets/yelp_review_full).

Il dataset contiene recensioni con rating da 1 a 5 stelle, mappate in etichette di sentiment:

| Stelle | Label originale | Sentiment |
|--------|----------------|-----------|
| 1-2    | 0-1            | negative  |
| 3      | 2              | neutral   |
| 4-5    | 3-4            | positive  |

La scelta di Yelp Review Full rispetto ad Amazon Polarity è motivata dalla presenza delle recensioni a 3 stelle, che costituiscono la classe `neutral`.

**Campionamento bilanciato:** 30.000 esempi per classe (90.000 totali) per evitare bias verso classi maggioritarie.

---

## Pipeline

Il modello è implementato come `sklearn.pipeline.Pipeline` con due step sequenziali:

```
Testo grezzo → TF-IDF Vectorizer → Logistic Regression → Sentiment
```

### TF-IDF Vectorizer

Trasforma il testo in un vettore numerico sparso. Ogni dimensione del vettore corrisponde a una parola (o bigramma) del vocabolario, con un peso che riflette l'importanza del termine nel documento rispetto al corpus.

| Parametro | Valore | Motivazione |
|-----------|--------|-------------|
| `max_features` | 50.000 | Limita la dimensionalità mantenendo i termini più informativi |
| `ngram_range` | (1, 2) | Include bigrammi per catturare negazioni ("not good", "not bad") |
| `sublinear_tf` | True | Scala logaritmica delle frequenze, riduce il peso di termini ripetuti |
| `min_df` | 2 | Ignora termini che appaiono in meno di 2 documenti (typo, nomi propri) |
| `strip_accents` | unicode | Normalizza caratteri accentati |
| `token_pattern` | `\b[a-zA-Z][a-zA-Z]+\b` | Accetta solo token alfabetici di almeno 2 caratteri |

**Perché i bigrammi sono importanti per il sentiment:**
```
"not good"  →  unigrammi: ["not", "good"]      ← ambiguo
            →  bigrammi:  ["not", "good", "not good"]  ← negazione catturata
```

### Logistic Regression

Classificatore lineare che impara un peso per ogni feature del vocabolario, uno per classe. La classe predetta è quella con il punteggio pesato più alto, convertito in probabilità tramite softmax.

| Parametro | Valore | Motivazione |
|-----------|--------|-------------|
| `C` | 1.0 | Regolarizzazione L2 di default, buon bilanciamento bias/varianza |
| `max_iter` | 1000 | Garantisce convergenza su dataset di grandi dimensioni |
| `class_weight` | balanced | Compensa automaticamente eventuali squilibri tra classi |
| `random_state` | 42 | Riproducibilità dei risultati |

---

## Risultati

```
Distribuzione classi: {'negative': 30000, 'neutral': 30000, 'positive': 30000}
Train: 72000 esempi | Test: 18000 esempi
```

### Metriche sul test set

| Classe    | Precision | Recall | F1-score |
|-----------|-----------|--------|----------|
| negative  | 0.81      | 0.82   | 0.82     |
| neutral   | 0.67      | 0.67   | 0.67     |
| positive  | 0.80      | 0.79   | 0.80     |

**Accuracy complessiva: 76.14%**

### Analisi dei risultati

- **negative e positive** ottengono F1 ~0.81 grazie a un vocabolario sentiment fortemente polarizzato ("terrible", "amazing", "recommend").
- **neutral** è la classe più difficile (F1 0.67): le recensioni a 3 stelle contengono sia termini positivi che negativi, rendendole ambigue. Questo è atteso e accettabile.

### Smoke test

```
✅ [POSITIVE] (0.96) → "This product is absolutely amazing! Best purchase ever."
✅ [NEGATIVE] (0.99) → "Terrible quality, broke after one day. Total waste of money."
✅ [NEUTRAL ] (0.75) → "It's okay, nothing special. Does the job I guess."
```

La confidence più bassa sul neutral (0.75 vs 0.96-0.99) riflette l'ambiguità intrinseca della classe.

---

## Output

Il modello addestrato viene serializzato in `app/model.pkl` tramite `pickle`.

Per rigenerare il modello:

```bash
python train.py
```

---