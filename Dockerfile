# Dockerfile
FROM docker.io/bitnami/kafka:3.3

# Install kcat
RUN apt-get install kafkacat
