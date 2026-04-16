# Sentiment Analysis — Deploy & Monitoring

Sistema end-to-end per il deploy e il monitoraggio di un modello di Sentiment Analysis:
training, API REST, pipeline CI/CD con Jenkins, monitoring con Prometheus e Grafana.

---

## Quickstart

### Prerequisiti

- Docker 24+ con plugin `compose`
- Git

### Avvio in 3 comandi

```bash
git clone https://github.com/FedeMotzo/sentiment-deploy.git
cd sentiment-deploy
docker compose up -d jenkins
```

### Setup Jenkins

1. Recupera la password iniziale:
   ```bash
   docker exec sentiment-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```
2. Apri <http://localhost:8080>, incolla la password
3. Seleziona **"Install suggested plugins"** e attendi che finisca
4. Crea un utente admin (es. `admin` / `admin`)
5. **Nuovo Elemento** → nome `sentiment-pipeline` → tipo **Pipeline** → OK
6. Nella sezione Pipeline:
   - *Definition*: **Pipeline script from SCM**
   - *SCM*: **Git**
   - *Repository URL*: `https://github.com/FedeMotzo/sentiment-deploy.git`
   - *Branch*: `*/main`
   - *Script Path*: `Jenkinsfile`
7. Salva → **Build Now**

La pipeline si occuperà di tutto: training del modello, test, build dell'immagine,
deploy di API + Prometheus + Grafana.

### URL di accesso (dopo il primo build)

| Servizio | URL | Credenziali |
|----------|-----|-------------|
| Jenkins | <http://localhost:8080> | admin / admin |
| API (Swagger) | <http://localhost:8000/docs> | — |
| Prometheus | <http://localhost:9090> | — |
| Grafana | <http://localhost:3000> | admin / admin |

### Smoke test dell'API

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"review":"This product is absolutely amazing!"}'
```

---

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
**Il file non è versionato in git**: viene generato dalla pipeline Jenkins oppure localmente.

Per rigenerare il modello in locale:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python train.py
```

---

# Step 2 — API REST con FastAPI

## Obiettivo

Esporre il modello di Sentiment Analysis tramite una API REST, rendendolo accessibile via HTTP. L'API gestisce la validazione dell'input, l'inferenza del modello e l'esposizione delle metriche per Prometheus.

---

## Struttura

```
app/
├── __init__.py
├── model.py    ← caricamento e inferenza del modello
├── metrics.py  ← definizione metriche Prometheus
└── main.py     ← FastAPI ed endpoint
```

---

## Componenti

### `model.py` — Inferenza

Gestisce il caricamento del pipeline sklearn e l'inferenza. Il modello viene caricato **una volta sola** all'avvio dell'API in una variabile globale `_pipeline`, evitando di rileggere il file `.pkl` ad ogni richiesta.

La funzione `predict()` restituisce sempre tre informazioni:
- `sentiment`: la classe predetta (`positive`, `negative`, `neutral`)
- `confidence`: la probabilità della classe predetta
- `probabilities`: le probabilità di tutte e tre le classi

### `metrics.py` — Metriche Prometheus

Definisce tre tipi di metriche:

| Metrica | Tipo | Descrizione |
|---------|------|-------------|
| `sentiment_predictions_total` | Counter | Numero totale di predizioni, per classe |
| `sentiment_prediction_errors_total` | Counter | Numero totale di errori |
| `sentiment_prediction_latency_seconds` | Histogram | Distribuzione dei tempi di risposta |
| `sentiment_cpu_usage_percent` | Gauge | Utilizzo CPU corrente |

**Differenza tra i tipi:**
- **Counter**: valore che cresce (es. numero di richieste totali)
- **Histogram**: registra la distribuzione di un valore nel tempo (es. quante richieste hanno risposto entro 10ms, 50ms, 100ms...)
- **Gauge**: valore istantaneo che può salire e scendere (es. CPU%)

### `main.py` — Applicazione FastAPI

Definisce l'applicazione e i tre endpoint. Usa il **lifespan** di FastAPI per caricare il modello allo start.

---

## Endpoint

### `POST /predict`

Classifica il sentiment di una recensione.

**Request:**
```json
{
  "review": "This product is absolutely amazing!"
}
```

**Response:**
```json
{
  "sentiment": "positive",
  "confidence": 0.8767,
  "probabilities": {
    "negative": 0.0820,
    "neutral":  0.0412,
    "positive": 0.8767
  }
}
```

**Validazione input** — gestita da Pydantic:
- Il campo `review` non può essere vuoto
- La recensione deve contenere almeno 3 caratteri
- In caso di input non valido, l'API restituisce `422 Unprocessable Entity`

**Aggiornamento metriche** — ad ogni chiamata:
- Incrementa `sentiment_predictions_total` con la label del sentiment predetto
- Registra la latenza in `sentiment_prediction_latency_seconds`
- In caso di errore, incrementa `sentiment_prediction_errors_total`

---

### `GET /metrics`

Espone tutte le metriche in formato testo leggibile da Prometheus.

```
# HELP sentiment_predictions_total Numero totale di predizioni eseguite
# TYPE sentiment_predictions_total counter
sentiment_predictions_total{sentiment="positive"} 42.0
sentiment_predictions_total{sentiment="negative"} 18.0
sentiment_predictions_total{sentiment="neutral"} 7.0
...
```

Prometheus chiama questo endpoint periodicamente e archivia i dati nel suo database.

---

### `GET /health`

Healthcheck per Docker e Jenkins. Restituisce `200 OK` se l'API è attiva.

```json
{ "status": "ok" }
```

Usato da:
- Docker per verificare che il container sia sano (`HEALTHCHECK`)
- Jenkins per verificare che il deploy sia andato a buon fine

---

# Step 3 — Docker e Monitoraggio

## Obiettivo

Containerizzare l'API e orchestrare l'intero stack (API + Prometheus + Grafana) tramite Docker Compose, garantendo riproducibilità dell'ambiente e monitoraggio in tempo reale.

---

## Struttura

```
├── Dockerfile                    ← API
├── docker-compose.yml
├── jenkins/
│   └── Dockerfile                ← Jenkins custom (Python + Docker CLI)
└── monitoring/
    ├── prometheus/
    │   ├── Dockerfile            ← Prometheus + config integrata
    │   └── prometheus.yml
    └── grafana/
        ├── Dockerfile            ← Grafana + provisioning integrato
        └── provisioning/
            ├── datasources/
            │   └── prometheus.yml      ← configura Prometheus come datasource
            └── dashboards/
                ├── dashboard.yml       ← dice a Grafana dove trovare le dashboard
                └── sentiment_dashboard.json  ← dashboard pre-configurata
```

Ogni servizio viene costruito con un Dockerfile dedicato che include la sua configurazione.
Questo approccio rende l'immagine autoconsistente e
permette a Jenkins (che gira in un container) di deployare senza problemi di path.

---

## Dockerfile dell'API

Il Dockerfile usa un **multi-stage build** per mantenere l'immagine finale il più leggera possibile.

```
Stage 1 (builder) → installa le dipendenze Python
Stage 2 (runtime) → copia solo il risultato, senza tool di build
```

Include un **guard** che fa fallire il build se `app/model.pkl` non è presente nel
build context, evitando deploy silenziosi di un'immagine senza modello.

---

## Docker Compose

Orchestra quattro servizi su una rete interna isolata (`sentiment-net`):

### Servizi

| Servizio | Immagine | Porta | Ruolo |
|----------|----------|-------|-------|
| `jenkins` | build locale | 8080 | Server CI/CD |
| `api` | `sentiment-api:latest` (built dalla pipeline) | 8000 | Serve il modello |
| `prometheus` | build locale | 9090 | Raccoglie metriche |
| `grafana` | build locale | 3000 | Visualizza dashboard |

### Volumi persistenti

- `jenkins-data` — conserva configurazione Jenkins, job, credenziali
- `prometheus-data` — conserva i dati storici delle metriche
- `grafana-data` — conserva configurazioni e preferenze Grafana

I dati sopravvivono al riavvio dei container.

---

## Prometheus

Scrapa l'endpoint `/metrics` dell'API ogni 15 secondi e archivia i dati nel suo database time-series.

```yaml
scrape_configs:
  - job_name: "sentiment-api"
    static_configs:
      - targets: ["api:8000"]  # nome servizio Docker, non localhost
```

---

## Grafana

### Provisioning automatico

Grafana viene configurata interamente tramite file, senza intervento manuale sulla UI. Al primo avvio carica automaticamente:

- **Datasource** (`provisioning/datasources/prometheus.yml`) — connessione a Prometheus
- **Dashboard** (`provisioning/dashboards/sentiment_dashboard.json`) — dashboard pre-configurata

### Dashboard — pannelli

| Pannello | Query Prometheus | Descrizione |
|----------|-----------------|-------------|
| Predizioni per sentiment | `rate(sentiment_predictions_total[1m])` | Frequenza predizioni al minuto per classe |
| Latenza p50/p95/p99 | `histogram_quantile(...)` | Distribuzione tempi di risposta |
| Errori | `rate(sentiment_prediction_errors_total[1m])` | Frequenza errori al minuto |
| CPU % | `sentiment_cpu_usage_percent` | Utilizzo CPU istantaneo |

---

# Step 4 — CI/CD con Jenkins

## Obiettivo

Automatizzare l'intero ciclo di training, test, build e deploy tramite una pipeline
Jenkins. Ogni commit scatena (o può scatenare) una build che addestra il modello,
esegue i test, costruisce l'immagine Docker e avvia lo stack completo.

---

## Architettura

Jenkins gira in un container Docker definito in `jenkins/Dockerfile`. Contiene:
- **Python 3.13** per eseguire training e test
- **Docker CLI** + **compose plugin** per costruire immagini e orchestrare container
- Accesso al Docker daemon dell'host tramite **socket montato** (`/var/run/docker.sock`)

---

## Stage della pipeline

La pipeline è definita in `Jenkinsfile` nella root del repo.

| # | Stage | Cosa fa |
|---|-------|---------|
| 1 | **Setup** | Crea un virtualenv Python e installa le dipendenze di `requirements.txt` |
| 2 | **Train Model** | Esegue `train.py` se `app/model.pkl` non esiste già |
| 3 | **Unit Test** | `pytest tests/test_unit.py` |
| 4 | **Integration Test** | `pytest tests/test_integration.py` |
| 5 | **Build Docker Image** | Costruisce `sentiment-api:${BUILD_NUMBER}` e tagga come `latest` |
| 6 | **Deploy** | `docker compose up -d --build api prometheus grafana` |

Ogni stage dipende dal successo del precedente: se i test falliscono, l'immagine
non viene costruita né deployata.

---

## Perché il training è dentro la pipeline

Il modello `app/model.pkl` non è committato nel repo: viene **prodotto dalla pipeline**.
Questo design ha due vantaggi:

- **Repo leggero**: niente binari da 30 MB che pesano sulla history di git
- **Riproducibilità**: chiunque cloni il repo ottiene un modello fresco dallo stesso dataset, con la stessa configurazione

Il training completo richiede circa 30 secondi su una macchina moderna.

---

## Configuration delle immagini — perché niente bind mount

Prometheus e Grafana **includono la loro configurazione direttamente nell'immagine**
tramite `COPY` in `monitoring/prometheus/Dockerfile` e `monitoring/grafana/Dockerfile`.

Questa scelta risolve un problema noto del pattern DooD (Docker-out-of-Docker):

> Quando Jenkins (dentro un container) esegue `docker compose up`, i path relativi
> dei bind mount come `./monitoring/prometheus.yml` vengono risolti **rispetto
> all'host**, non rispetto al workspace di Jenkins. Se il repo è clonato nel
> workspace Jenkins, l'host non lo vede e i mount falliscono.

Copiando i file di configurazione dentro l'immagine al build time, il problema
scompare: i file vengono passati via **build context**, non
via filesystem dell'host. Così la pipeline è portabile su qualsiasi macchina che
abbia Docker.

---

## Comandi utili

```bash
# Log della pipeline in real-time
docker logs -f sentiment-jenkins

# Stato di tutti i container
docker ps --format "table {{.Names}}\t{{.Status}}"

# Log dell'API (utile per debug dopo deploy)
docker logs sentiment-api --tail 50

# Stop completo (conserva i volumi)
docker compose down

# Reset totale (elimina anche dati storici e configurazione Jenkins)
docker compose down -v
```