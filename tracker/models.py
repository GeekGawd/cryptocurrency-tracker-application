from django.db import models
import uuid

# Create your models here.

class TimeStampable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True

class CoinAlert(TimeStampable, models.Model):
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)