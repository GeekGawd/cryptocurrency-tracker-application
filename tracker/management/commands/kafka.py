from django.core.management.base import BaseCommand
import json
import websocket
import psycopg
import threading
from kafka import KafkaProducer
from aiokafka import AIOKafkaConsumer
import asyncio
import time
import django
from django.conf import settings

producer = KafkaProducer(
    bootstrap_servers=["localhost:9093"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# ws = None
is_changed = False


def on_message(ws, message):
    global is_changed
    if is_changed:
        ws.close()
        is_changed = False
    data = json.loads(message)
    try:
        coin_name = data["stream"].rsplit("usdt", 1)[0]
        topic = f"{coin_name}-topic"
        producer.send(
            topic,
            {
                "ask_price": data["data"]["a"],
                "coin_name": coin_name,
                "bid_price": data["data"]["b"],
            },
        )
    except KeyError:
        print("Error in reading the price")


def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### closed ###")


def on_open(ws):
    from tracker.models import CoinSymbol

    coin_symbols = CoinSymbol.objects.values("symbol", "kafka_topic")
    binance_params = [
        f"{coin['symbol'].lower()}usdt@bookTicker" for coin in coin_symbols
    ]
    payload = {"method": "SUBSCRIBE", "params": binance_params, "id": 1}
    ws.send(json.dumps(payload))


def listen_notify():
    global is_changed
    conn = psycopg.connect(
        dbname="tanxfi",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432",
        autocommit=True,
    )
    conn.execute("LISTEN tracker_coinsymbol")
    gen = conn.notifies()
    for notify in gen:
        producer.send("tracker_coinsymbol", {"topic_name": notify.payload})
        is_changed = True


def binance_websockets():
    ws = websocket.WebSocketApp(
        "wss://stream.binance.com/stream",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()


def start_producer():
    django.setup()
    thread = threading.Thread(target=listen_notify)
    thread.daemon = True
    thread.start()
    try:
        while True:
            binance_websockets()
            print("Restaring the websocket")
            time.sleep(2)
    except KeyboardInterrupt:
        print("Exiting")


async def kafka_consumer(kafka_topic):
    from tracker.models import CoinAlert, COIN_ALERT_STATUS, COIN_ALERT_INTENTION

    print("Started the consumer", kafka_topic)
    consumer = AIOKafkaConsumer(
        kafka_topic,
        bootstrap_servers="localhost:9093",
        auto_offset_reset="latest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    await consumer.start()
    try:
        lowest_available_buy_price = float("inf")
        highest_available_sell_price = float("-inf")
        count = 0
        async for message in consumer:
            lowest_available_buy_price = min(
                lowest_available_buy_price, float(message.value["ask_price"])
            )
            highest_available_sell_price = max(
                highest_available_sell_price, float(message.value["bid_price"])
            )
            count += 1
            if count >= settings.KAFKA_BATCH_SIZE:
                print(
                    lowest_available_buy_price,
                    highest_available_sell_price,
                    message.value["coin_name"],
                )
                await CoinAlert.objects.filter(
                    coin_symbol__symbol=message.value["coin_name"],
                    threshold_price__gte=lowest_available_buy_price,
                    status=COIN_ALERT_STATUS[0][0],
                    buy_or_sell=COIN_ALERT_STATUS[0][0],
                ).aupdate(status=COIN_ALERT_STATUS[1][0])
                await CoinAlert.objects.filter(
                    coin_symbol__symbol=message.value["coin_name"],
                    threshold_price__lte=highest_available_sell_price,
                    status=COIN_ALERT_STATUS[0][0],
                    buy_or_sell=COIN_ALERT_INTENTION[1][0],
                ).aupdate(status=COIN_ALERT_STATUS[1][0])
                count = 0
    finally:
        await consumer.stop()


async def listen_tracker_coinsymbol():
    print("Listening for changes")
    consumer = AIOKafkaConsumer(
        "tracker_coinsymbol",
        bootstrap_servers="localhost:9093",
        auto_offset_reset="latest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    await consumer.start()
    try:
        async for message in consumer:
            asyncio.create_task(kafka_consumer(message.value["topic_name"]))
    finally:
        await consumer.stop()


def start_consumer():
    django.setup()
    from tracker.models import CoinSymbol

    loop = asyncio.get_event_loop()
    coin_symbols = CoinSymbol.objects.values("symbol", "kafka_topic")
    tasks = [
        loop.create_task(kafka_consumer(coin_symbol["kafka_topic"]))
        for coin_symbol in coin_symbols
    ]
    tasks.append(loop.create_task(listen_tracker_coinsymbol()))
    loop.run_until_complete(asyncio.gather(*tasks))


class Command(BaseCommand):
    help = "Starts the websocket app"

    def handle(self, *args, **options):
        from multiprocessing import Process

        producer_process = Process(target=start_producer)
        consumer_process = Process(target=start_consumer)

        producer_process.start()
        consumer_process.start()

        producer_process.join()
        consumer_process.join()
