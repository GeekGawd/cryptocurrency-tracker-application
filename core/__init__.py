from apscheduler.schedulers.background import BackgroundScheduler
from decouple import config
if config("BACKGROUND_TASKS", default=True, cast=bool):
    scheduler = BackgroundScheduler()

    from tracker.tasks import *

    scheduler.start()