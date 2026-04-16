pipeline {
    agent any

    environment {
        IMAGE_NAME   = "sentiment-api"
        IMAGE_TAG    = "${BUILD_NUMBER}"
        PYTHON_IMAGE = "python:3.11-slim"
        MODEL_PATH   = "app/model.pkl"
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    stages {

        // ── 1. TRAIN ─────────────────────────────────────────────────────────
        // Genera il modello scikit-learn se non esiste già.
        stage('Train Model') {
            steps {
                echo "Training del modello di sentiment analysis..."
                sh '''
                    if [ -f "${MODEL_PATH}" ]; then
                        echo "Modello già presente in ${MODEL_PATH}, salto il training."
                    else
                        docker run --rm \
                            -v "$PWD":/app \
                            -w /app \
                            ${PYTHON_IMAGE} \
                            bash -c "
                                pip install --no-cache-dir --quiet -r requirements.txt &&
                                python scripts/train.py
                            "
                    fi
                    test -f "${MODEL_PATH}" || { echo '❌ model.pkl non generato'; exit 1; }
                    echo "✅ Modello pronto: $(ls -lh ${MODEL_PATH} | awk '{print $5}')"
                '''
            }
        }

        // ── 2. UNIT TEST ─────────────────────────────────────────────────────
        stage('Unit Test') {
            steps {
                echo "Esecuzione unit test..."
                sh '''
                    docker run --rm \
                        -v "$PWD":/app \
                        -w /app \
                        ${PYTHON_IMAGE} \
                        bash -c "
                            pip install --no-cache-dir --quiet -r requirements.txt &&
                            python -m pytest tests/test_unit.py -v
                        "
                '''
            }
        }

        // ── 3. INTEGRATION TEST ──────────────────────────────────────────────
        stage('Integration Test') {
            steps {
                echo "Esecuzione integration test..."
                sh '''
                    docker run --rm \
                        -v "$PWD":/app \
                        -w /app \
                        ${PYTHON_IMAGE} \
                        bash -c "
                            pip install --no-cache-dir --quiet -r requirements.txt &&
                            python -m pytest tests/test_integration.py -v
                        "
                '''
            }
        }

        // ── 4. BUILD DOCKER IMAGE ────────────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                echo "Build dell'immagine ${IMAGE_NAME}:${IMAGE_TAG}..."
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
            }
        }

        // ── 5. DEPLOY ────────────────────────────────────────────────────────
        stage('Deploy') {
            steps {
                echo "Deploy dello stack (api + prometheus + grafana)..."
                sh 'docker compose up -d --no-deps --build api prometheus grafana'
            }
        }

        // ── 6. HEALTH CHECK ──────────────────────────────────────────────────
        stage('Health Check') {
            steps {
                echo "Verifica che l'API risponda..."
                sh '''
                    for i in $(seq 1 12); do
                        if curl -fsS http://sentiment-api:8000/health > /dev/null; then
                            echo "✅ API up"
                            exit 0
                        fi
                        echo "Tentativo $i/12 - attendo 5s..."
                        sleep 5
                    done
                    echo "❌ API non risponde"
                    docker logs sentiment-api --tail 50 || true
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline OK - immagine ${IMAGE_NAME}:${IMAGE_TAG} in esecuzione"
        }
        failure {
            echo "❌ Pipeline fallita allo stage: ${env.STAGE_NAME}"
        }
    }
}