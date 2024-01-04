from django.core.management.base import BaseCommand
import json
import websocket
import psycopg
import threading
from kafka import KafkaProducer
import time
from django.conf import settings
from decouple import config
from tracker.models import CoinSymbol

producer = KafkaProducer(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

is_changed = False

class Command(BaseCommand):
    help = "Starts the websocket app"

    def on_message(self, ws, message):
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


    def on_error(self, ws, error):
        print(error)


    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")


    def on_open(self, ws):

        coin_symbols = CoinSymbol.objects.values("symbol", "kafka_topic")
        binance_params = [
            f"{coin['symbol'].lower()}usdt@bookTicker" for coin in coin_symbols
        ]
        payload = {"method": "SUBSCRIBE", "params": binance_params, "id": 1}
        ws.send(json.dumps(payload))


    def listen_notify(self):
        global is_changed
        conn = psycopg.connect(
            dbname=config("POSTGRES_DB_NAME", default="tanxfi"),
            user=config("POSTGRES_DB_USER", default="postgres"),
            password=config("POSTGRES_DB_PASSWORD", default="admin"),
            host=config("POSTGRES_DB_HOST", default="db"),
            port=config("POSTGRES_DB_PORT", default="5432"),
            autocommit=True,
        )
        conn.execute("LISTEN tracker_coinsymbol")
        gen = conn.notifies()
        for notify in gen:
            producer.send("tracker_coinsymbol", {"topic_name": notify.payload})
            is_changed = True

    def binance_websockets(self):
        ws = websocket.WebSocketApp(
            "wss://stream.binance.com/stream",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        ws.run_forever()

    def handle(self, *args, **options):
        thread = threading.Thread(target=self.listen_notify)
        thread.daemon = True
        thread.start()
        try:
            while True:
                self.binance_websockets()
                print("Restaring the websocket")
                time.sleep(2)
        except KeyboardInterrupt:
            print("Exiting")