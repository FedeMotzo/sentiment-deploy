pipeline {
    agent any

    environment {
        IMAGE_NAME = "sentiment-api"
        IMAGE_TAG  = "${BUILD_NUMBER}"
    }

    stages {

        // ── 1. INITIALIZE ────────────────────────────────────────────────────
        // Configura il PATH con il Docker installato tramite Global Tool Configuration
        stage('Initialize') {
            steps {
                script {
                    def dockerHome = tool 'myDocker'
                    env.PATH = "${dockerHome}/bin:${env.PATH}"
                }
                echo "Docker path configurato: ${env.PATH}"
            }
        }

        // ── 2. TEST ──────────────────────────────────────────────────────────
        stage('Unit Test') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    reuseNode true
                }
            }
            steps {
                echo "Esecuzione unit test..."
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