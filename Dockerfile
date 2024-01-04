FROM python:3.11

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . /app/
    
RUN pip install daphne
RUN pip install -r requirements.txt