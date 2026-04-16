pipeline {
    agent any

    environment {
        IMAGE_NAME = "sentiment-api"
        IMAGE_TAG  = "${BUILD_NUMBER}"
    }

    stages {

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

        stage('Train Model') {
            steps {
                echo "Training del modello..."
                sh '''
                    if [ -f "app/model.pkl" ]; then
                        echo "Modello già presente, skip."
                    else
                        . .venv/bin/activate
                        python train.py
                    fi
                '''
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m pytest tests/test_unit.py -v
                '''
            }
        }

        stage('Integration Test') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m pytest tests/test_integration.py -v
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker compose up -d --no-deps --build api prometheus grafana
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    sleep 15
                    curl -f http://sentiment-api:8000/health || exit 1
                    echo "✅ API OK"
                '''
            }
        }
    }

    post {
        success { echo "✅ Pipeline OK — ${IMAGE_NAME}:${IMAGE_TAG}" }
        failure { echo "❌ Pipeline fallita allo stage: ${env.STAGE_NAME}" }
        always  { sh "rm -rf .venv || true" }
    }
}