pipeline {
    agent any

    environment {
        IMAGE_NAME = "sentiment-api"
        IMAGE_TAG  = "${BUILD_NUMBER}"
        PATH = "/usr/local/bin:/Applications/Docker.app/Contents/Resources/bin:${env.PATH}"
    }

    stages {

        // ── 1. CHECKOUT ──────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "Checkout del repository..."
                checkout scm
            }
        }

        // ── 2. TEST ──────────────────────────────────────────────────────────
        // Eseguiti dentro un container Python con reuseNode true:
        // il container condivide il workspace dell'agent Jenkins
        stage('Unit Test') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    reuseNode true  // condivide workspace e node con l'agent principale
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
                    reuseNode true
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

        // ── 3. BUILD DOCKER IMAGE ────────────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                echo "Build dell'immagine Docker..."
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
            }
        }

        // ── 4. DEPLOY ────────────────────────────────────────────────────────
        stage('Deploy') {
            steps {
                echo "Deploy dello stack..."
                sh '''
                    docker compose down --remove-orphans || true
                    docker compose up -d --build
                '''
            }
        }

        // ── 5. HEALTH CHECK ──────────────────────────────────────────────────
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
    }
}