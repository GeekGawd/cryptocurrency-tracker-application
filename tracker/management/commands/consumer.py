from django.core.management.base import BaseCommand
from aiokafka import AIOKafkaConsumer
from tracker.models import CoinSymbol
import asyncio

class Command(BaseCommand):
    help = "Starts the websocket app"

    async def kafka_consumer(self, kafka_topic):
        print("Started the consumer", kafka_topic)
        consumer = AIOKafkaConsumer(
            kafka_topic,
            bootstrap_servers='localhost:9093',
            auto_offset_reset='latest',
            value_deserializer=lambda v: float(v.decode("utf-8"))
        )
        await consumer.start()
        try:
            async for message in consumer:
                print(message.value)
        finally:
            await consumer.stop()

    async def listen_tracker_coinsymbol(self):
        print("Listening for changes")
        consumer = AIOKafkaConsumer(
            'tracker_coinsymbol',
            bootstrap_servers='localhost:9093',
            auto_offset_reset='latest',
            value_deserializer=lambda v: v.decode("utf-8")
        )
        await consumer.start()
        try:
            async for message in consumer:
                asyncio.create_task(self.kafka_consumer(message.value))
        finally:
            await consumer.stop()

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        coin_symbols = CoinSymbol.objects.values("symbol", "kafka_topic")
        tasks = [loop.create_task(self.kafka_consumer(coin_symbol["kafka_topic"])) for coin_symbol in coin_symbols]
        tasks.append(loop.create_task(self.listen_tracker_coinsymbol()))
        loop.run_until_complete(asyncio.gather(*tasks))
