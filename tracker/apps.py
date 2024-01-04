from django.apps import AppConfig
from kafka import KafkaConsumer
from django.conf import settings
from django.db import connection

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'

    def ready(self) -> None:
        pass
        # coin_symbol_table_name = "tracker_coinsymbol"

        # kafka_consumers = dict()

        # with connection.cursor() as cursor:
        #     cursor.execute(f"SELECT * FROM {coin_symbol_table_name}")
        #     coin_symbols = cursor.fetchall()
        
        # for coin in coin_symbols:
        #     coin_name = coin[1]
        #     kafka_coin_topic_name = coin[4]
        #     kafka_consumers[coin_name] = KafkaConsumer(
        #         kafka_coin_topic_name,
        #         bootstrap_servers=[settings.KAFKA_BOOTSTRAP_SERVER],
        #         auto_offset_reset='earliest',
        #     )



