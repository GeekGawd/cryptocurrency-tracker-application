from celery import shared_task
import random, time
from django.core.mail import EmailMessage
from tracker.models import OTP
from rest_framework.response import Response

