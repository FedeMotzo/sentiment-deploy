pipeline {
    agent none  // nessun agent globale — ogni stage dichiara il suo

    environment {
        IMAGE_NAME = "sentiment-api"
        IMAGE_TAG  = "${BUILD_NUMBER}"
    }

    stages {

        // ── 1. TEST ──────────────────────────────────────────────────────────
        // Eseguiti dentro un container Python
        stage('Unit Test') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                echo "Installazione dipendenze ed esecuzione unit test..."
                sh '''
                    pip install -r requirements.txt --quiet
                    python -m pytest tests/test_unit.py -v
                '''
            }
        }

        stage('Integration Test') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                echo "Esecuzione integration test..."
                sh '''
                    pip install -r requirements.txt --quiet
                    python -m pytest tests/test_integration.py -v
                '''
            }
        }

        // ── 2. BUILD E DEPLOY ─────────────────────────────────────────────────
        stage('Build Docker Image') {
            agent any
            steps {
                echo "Build dell'immagine Docker..."
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Deploy') {
            agent any
            steps {
                echo "Deploy stack..."
                sh '''
                    docker compose down --remove-orphans || true
                    docker compose up -d --build
                '''
            }
        }

        stage('Health Check') {
            agent any
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
            echo "✅ Pipeline completata con successo! Immagine: ${IMAGE_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo "❌ Pipeline fallita al stage: ${env.STAGE_NAME}"
        }
    }
}