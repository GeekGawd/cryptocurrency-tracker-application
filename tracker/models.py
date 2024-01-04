import requests
from django.db import models
import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from rest_framework_simplejwt.tokens import RefreshToken
from core.behaviours import TimeStampable
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(update_fields=["is_staff", "is_superuser", "is_active"])
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def generate_token(self):
        refresh = RefreshToken.for_user(self)
        return str(refresh), str(refresh.access_token)

    def tokens(self):
        refresh, access = self.generate_token()
        return {"refresh": refresh, "access": access}

    def refresh(self):
        refresh, _ = self.generate_token()
        return refresh

    def access(self):
        _, access = self.generate_token()
        return access


COIN_ALERT_STATUS = (
    ("untriggered", "UNTRIGGERED"),
    ("triggered", "TRIGGERED"),
    ("mail_sent", "MAIL_SENT"),
)

class CoinSymbol(models.Model):
    symbol = models.CharField(max_length=255, unique=True)
    kafka_topic = models.CharField(max_length=255, unique=True, blank=True, null=True)
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.symbol

    def clean(self) -> None:
        response = requests.get(
            f"https://api.binance.com/api/v3/ticker/price?symbol={self.symbol.upper()}USDT"
        )
        if response.status_code >= 400:
            raise ValidationError(
                {"symbol": "Invalid symbol, Refer the Binanace API for valid symbols"}
            )

    def save(self, *args, **kwargs):
        if not self.kafka_topic:
            self.kafka_topic = f"{self.symbol}-topic"
        super().save(*args, **kwargs)

COIN_ALERT_INTENTION = (
    ("buy", "BUY"),
    ("sell", "SELL"),
)
class CoinAlert(TimeStampable, models.Model):
    coin_symbol = models.ForeignKey(
        CoinSymbol, on_delete=models.CASCADE, related_name="coin_symbol"
    )
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(
        choices=COIN_ALERT_STATUS, max_length=20, default=COIN_ALERT_STATUS[0][0]
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="coin_alert_user"
    )
    threshold_price = models.FloatField()
    buy_or_sell = models.CharField(
        choices=COIN_ALERT_INTENTION, max_length=20
    )

    @property
    def alert_email(self) -> EmailMessage:
        coin_symbol = self.coin_symbol.symbol
        return EmailMessage(
            subject=f"Alert for {coin_symbol}",
            body=f"Alert for {coin_symbol} has been triggered for price {self.threshold_price} and intention {self.buy_or_sell}",
            to=[self.user.email],
        )
