pipeline {
    agent any

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
    }
}