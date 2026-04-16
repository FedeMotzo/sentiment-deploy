FROM jenkins/jenkins:2.462.3-lts-jdk17

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        docker.io \
        docker-compose-plugin \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -f docker && usermod -aG docker jenkins

USER jenkins