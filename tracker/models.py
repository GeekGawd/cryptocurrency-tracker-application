from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from rest_framework_simplejwt.tokens import RefreshToken
from core.behaviours import TimeStampable

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(update_fields=['is_staff', 'is_superuser', 'is_active'])
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def generate_token(self):
        refresh = RefreshToken.for_user(self)
        return str(refresh), str(refresh.access_token)

    def tokens(self):
        refresh, access = self.generate_token()
        return {
            'refresh': refresh,
            'access': access
        }

    def refresh(self):
        refresh, _ = self.generate_token()
        return refresh
    
    def access(self):
        _, access = self.generate_token()
        return access

COIN_ALERT_STATUS = (
    ('untriggered', 'UNTRIGGERED'),
    ('triggered', 'TRIGGERED'),
)

class CoinAlert(TimeStampable, models.Model):
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(choices=COIN_ALERT_STATUS, max_length=20, default=COIN_ALERT_STATUS[0][0])

class OTP(TimeStampable, models.Model):
    otp = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_user")
    
    def __str__(self):
        return f"{self.otp_email} : {self.otp}"