from rest_framework import serializers
from .models import User


class UserStatusSerializer(serializers.Serializer):
    """Serializer for user status response"""
    exists = serializers.BooleanField()
    is_active = serializers.BooleanField()
    phone_number = serializers.CharField()
    name = serializers.CharField(required=False, allow_null=True)
    subscription_start_date = serializers.DateTimeField(required=False, allow_null=True)
    subscription_end_date = serializers.DateTimeField(required=False, allow_null=True)
    package_type = serializers.IntegerField(required=False, allow_null=True)


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for payment initiation request"""
    phone_number = serializers.CharField(required=True)
    amount = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True)


class PaymentResponseSerializer(serializers.Serializer):
    """Serializer for payment initiation response"""
    order_id = serializers.CharField()
    payment_url = serializers.URLField()
    status = serializers.CharField()
    message = serializers.CharField(required=False)


class WebhookSerializer(serializers.Serializer):
    """Serializer for Zeno Pay webhook"""
    status = serializers.CharField()
    buyer_phone = serializers.CharField()
    amount = serializers.CharField()
    order_id = serializers.CharField(required=False, allow_blank=True)
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.CharField(required=False, allow_blank=True)
