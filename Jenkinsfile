pipeline {
    agent any

    environment {
        IMAGE_NAME = "sentiment-api"
        IMAGE_TAG  = "${BUILD_NUMBER}"
    }

    stages {

        // ── 1. SETUP ─────────────────────────────────────────────────────────
        stage('Setup') {
            steps {
                echo "Setup ambiente Python..."
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip --quiet
                    pip install -r requirements.txt --quiet
                '''
            }
        }

        // ── 2. UNIT TEST ─────────────────────────────────────────────────────
        stage('Unit Test') {
            steps {
                echo "Esecuzione unit test..."
                sh '''
                    . .venv/bin/activate
                    python -m pytest tests/test_unit.py -v
                '''
            }
        }

        // ── 3. INTEGRATION TEST ──────────────────────────────────────────────
        stage('Integration Test') {
            steps {
                echo "Esecuzione integration test..."
                sh '''
                    . .venv/bin/activate
                    python -m pytest tests/test_integration.py -v
                '''
            }
        }

        // ── 4. BUILD DOCKER IMAGE ────────────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                echo "Build dell'immagine Docker..."
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
            }
        }

        // ── 5. DEPLOY ────────────────────────────────────────────────────────
        stage('Deploy') {
            steps {
                echo "Deploy dello stack..."
                sh '''
                    docker compose down --remove-orphans || true
                    docker compose up -d --build
                '''
            }
        }

        // ── 6. HEALTH CHECK ──────────────────────────────────────────────────
        stage('Health Check') {
            steps {
                echo "Verifica che l'API sia up..."
                sh '''
                    sleep 15
                    curl -f http://localhost:8000/health || exit 1
                    echo "✅ API risponde correttamente"
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completata! Immagine: ${IMAGE_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo "❌ Pipeline fallita al stage: ${env.STAGE_NAME}"
        }
        always {
            sh "rm -rf .venv || true"
        }
    }
}