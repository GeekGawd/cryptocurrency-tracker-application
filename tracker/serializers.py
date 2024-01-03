from rest_framework.exceptions import ValidationError
import re
from django.utils.translation import gettext_lazy as _
from tracker.models import User, CoinAlert
from rest_framework import serializers
import requests


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "password", "name")
        extra_kwargs = {
            "password": {
                "write_only": True,
                "min_length": 5,
                "required": True,
                "error_messages": {"required": "Password needed"},
            },
            "email": {
                "required": True,
                "error_messages": {"required": "Email field may not be blank."},
            },
            "name": {
                "required": True,
                "error_messages": {"required": "Name field may not be blank."},
            },
        }

    def validate_password(self, password):
        if not re.findall("\d", password):
            raise ValidationError(
                _("The password must contain at least 1 digit, 0-9."),
                code="password_no_number",
            )
        if not re.findall("[A-Z]", password):
            raise ValidationError(
                _("The password must contain at least 1 uppercase letter, A-Z."),
                code="password_no_upper",
            )
        if not re.findall("[a-z]", password):
            raise ValidationError(
                _("The password must contain at least 1 lowercase letter, a-z."),
                code="password_no_lower",
            )

        return password

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def to_representation(self, instance):
        data = super(UserSerializer, self).to_representation(instance)
        user = instance
        data["access"] = user.access()
        data["refresh"] = user.refresh()

        return data


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoinAlert
        exclude = ["id", "user"]
        read_only_fields = ["status", "user"]

    def validate_coin_symbol(self, value):
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={value}USDT"
        response = requests.get(url)
        if response.status_code >= 400:
            raise serializers.ValidationError(
                "Invalid coin symbol, Please Refer to Binance API for valid symbols"
            )
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        if CoinAlert.objects.filter(
            user=validated_data["user"],
            coin_symbol=validated_data["coin_symbol"],
            threshold_price=validated_data["threshold_price"],
            status="untriggered"
        ).exists():
            raise ValidationError({"message": "Coin Alert already exists"})
        return super().create(validated_data)
