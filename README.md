# Cryptocurrency Price Alert System Made With Django, DRF, Apache Kafka, Redis and PostgreSQL

The postman collection url is available on: [Postman Collection URL](https://documenter.getpostman.com/view/21779136/2s9YsGjDzS)


You can create alerts on different cryptocurrency and you will automatically get notified through email whenever the price meets the criteria. This project uses the Binance Websockets to get the price details.
## Run on Windows

Download [Python Version 3.11](https://www.python.org/downloads/release/python-3117/) and enter the following commands to activate virtualenv with python 3.11.

```bash
pip install virtualenv
virtualenv venv --python=3.11
./venv/Scripts/activate
```

Install requirements and daphne
```bash
pip install daphne
pip install -r requirements.txt
```

Run the django server, kafka producer and kafka consumer
```powershell
python manage.py runserver
python manage.py kafka 
python manage.py consumer
```

## Run using Docker

Just run `docker compose up -d` and docker containers will spin up for the application.

## Design Choices

- Django and DRF: They are very easy to develop and with recent Django 5.0 update it has become asynchronous. Though I used in a very limited fashion and didn't take full advantage of async. 

- Kafka: Using Kafka was extremely important as I can't just hit the database each time on every tick from binance websockets it will put a lot of load on the database. So, I send the ticks or message of the websockets to the kafka producer where each cryptocurrency has a separate topic/queue and the consumer listens to these topics checks and updates the alerts as `TRIGGERED`.

- PostgreSQL: Very robust and my database of choice for most projects. Though with crypto and stocks, a time series database is usually used but there was no need for that in this project. However, one feature of PostgreSQL is extremely important for this project and that was `LISTEN/NOTIFY` I used this to listen for Insert Calls in Database, so lets say I want to add support for a cryptocurrency, I get notified and following three things happen programmatically in the backend:
1. The websocket connection closes and subscribes to the new cryptocurrency.
2. A topic gets created for the new cryptocurrency and ticks from binance websocket is sent to it.
3. A new consumer is created which listens to the changes and updates the database.
   
- Redis: It is a In-Memory Database used to cache the list response of the DRF View. Nothing fancy and it is extremely easy to setup and use thanks to Django.