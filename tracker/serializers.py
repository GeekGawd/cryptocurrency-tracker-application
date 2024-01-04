from rest_framework.exceptions import ValidationError
import re
from django.utils.translation import gettext_lazy as _
from tracker.models import User, CoinAlert, CoinSymbol
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
        exclude = ["id", "user", "coin_symbol"]
        read_only_fields = ["status", "user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        coin_symbol_text = self.initial_data["coin_symbol"]
        try:
            coin_symbol = CoinSymbol.objects.get(symbol__iexact=coin_symbol_text)
        except CoinSymbol.DoesNotExist:
            raise ValidationError({"message": "Coin Symbol does not exist"})
        validated_data["coin_symbol"] = coin_symbol
        if CoinAlert.objects.filter(
            coin_symbol = coin_symbol,
            user=validated_data["user"],
            threshold_price=validated_data["threshold_price"],
            status="untriggered",
            buy_or_sell=validated_data["buy_or_sell"],
        ).exists():
            raise ValidationError({"message": "Coin Alert already exists"})
        return super().create(validated_data)
