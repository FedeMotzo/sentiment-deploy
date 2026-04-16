pipeline {
    agent any

    environment {
        IMAGE_NAME = "sentiment-api"
        IMAGE_TAG  = "${BUILD_NUMBER}"
    }

    stages {
        stage('Setup') {
            steps {
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
                sh '''
                    . .venv/bin/activate
                    if [ -f "app/model.pkl" ]; then
                        echo "Modello già presente, skip."
                    else
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
                sh 'docker compose up -d api prometheus grafana'
            }
        }
    }
}