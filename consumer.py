from kafka import KafkaConsumer
import json
consumer = KafkaConsumer(
    'posts',
    bootstrap_servers=['localhost:9093'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
)
# note that this for loop will block forever to wait for the next message
# following to asyncio, this should be done in a separate thread

for message in consumer:
    print(message.value)