from django.core.management.base import BaseCommand
from aiokafka import AIOKafkaConsumer
from tracker.models import CoinSymbol
import asyncio
import json
from django.conf import settings
from tracker.models import CoinAlert, COIN_ALERT_STATUS, COIN_ALERT_INTENTION


class Command(BaseCommand):
    help = "Starts the websocket app"

    async def kafka_consumer(self, kafka_topic):
        consumer = AIOKafkaConsumer(
            kafka_topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER,
            auto_offset_reset="latest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await consumer.start()
        print("Started the consumer", kafka_topic)
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

    async def listen_tracker_coinsymbol(self):
        print("Listening for changes")
        consumer = AIOKafkaConsumer(
            "tracker_coinsymbol",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER,
            auto_offset_reset="latest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await consumer.start()
        try:
            async for message in consumer:
                asyncio.create_task(self.kafka_consumer(message.value["topic_name"]))
        finally:
            await consumer.stop()

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        coin_symbols = CoinSymbol.objects.values("symbol", "kafka_topic")
        tasks = [
            loop.create_task(self.kafka_consumer(coin_symbol["kafka_topic"]))
            for coin_symbol in coin_symbols
        ]
        tasks.append(loop.create_task(self.listen_tracker_coinsymbol()))
        loop.run_until_complete(asyncio.gather(*tasks))
