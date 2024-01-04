from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()

from tracker.tasks import *

scheduler.start()