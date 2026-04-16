FROM jenkins/jenkins:lts

USER root

# Installa Python 3 e Docker CLI
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    docker.io \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Aggiunge jenkins al gruppo docker per accedere al socket
RUN groupadd -f docker && usermod -aG docker jenkins

USER jenkins