"""
metrics.py — Definizione delle metriche Prometheus

Le metriche vengono registrate globalmente e aggiornate ad ogni richiesta.
L'endpoint GET /metrics le espone in formato testo leggibile da Prometheus.

Tipi di metriche usate:
- Counter:   valore che può solamente crescere (es. numero di richieste)
- Histogram: distribuzione di valori (es. tempi di risposta)
- Gauge:     valore che può salire e scendere (es. uso memoria)
"""

from prometheus_client import Counter, Histogram, Gauge, REGISTRY
import psutil
import os


# ─── CONTATORI ────────────────────────────────────────────────────────────────

# Numero totale di richieste a /predict, suddivise per sentiment predetto
PREDICTIONS_TOTAL = Counter(
    name="sentiment_predictions_total",
    documentation="Numero totale di predizioni eseguite",
    labelnames=["sentiment"], # Etichetta con sentimento etichettato
)

# Numero di errori durante la predizione
PREDICTION_ERRORS_TOTAL = Counter(
    name="sentiment_prediction_errors_total",
    documentation="Numero totale di errori durante la predizione",
)

# ─── ISTOGRAMMA ──────────────────────────────────────────────────────────────

# Distribuzione dei tempi di risposta dell'endpoint /predict
# I bucket definiscono i diversi intervalli in secondi:
# quante richieste hanno risposto entro 10ms, 50ms, 100ms, ecc.
PREDICTION_LATENCY = Histogram(
    name="sentiment_prediction_latency_seconds",
    documentation="Latenza delle richieste di predizione in secondi",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

# ─── GAUGE ───────────────────────────────────────────────────────────────────

# Utilizzo corrente della CPU e della memoria
# Aggiornati ad ogni chiamata a /metrics
CPU_USAGE = Gauge(
    name="sentiment_cpu_usage_percent",
    documentation="Utilizzo corrente della CPU in percentuale",
)


def update_system_metrics():
    """
    Aggiorna le metriche di sistema (CPU).
    Chiamata ad ogni richiesta a GET /metrics.
    """
    CPU_USAGE.set(psutil.cpu_percent(interval=None))