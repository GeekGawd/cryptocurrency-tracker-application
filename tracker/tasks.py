from core import scheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.core import mail

five_minute_interval = IntervalTrigger(minutes=5)

@scheduler.scheduled_job(five_minute_interval)
def send_email_alert():
    print("email send")
    from tracker.models import CoinAlert, COIN_ALERT_STATUS
    coin_alerts_triggered = CoinAlert.objects.filter(status=COIN_ALERT_STATUS[1][0])
    connection = mail.get_connection()
    email_messages = [alert.alert_email for alert in coin_alerts_triggered]
    CoinAlert.objects.filter(status=COIN_ALERT_STATUS[1][0]).update(
        status=COIN_ALERT_STATUS[2][0]
    )
    connection.send_messages(email_messages)
