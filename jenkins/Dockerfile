FROM jenkins/jenkins:lts

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER jenkins