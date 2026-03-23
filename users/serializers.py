from django.conf import settings
from rest_framework import serializers
from .models import User
from .services import BiasharaPayService


class UserStatusSerializer(serializers.Serializer):
    """Serializer for user status response"""
    exists = serializers.BooleanField()
    is_active = serializers.BooleanField()
    phone_number = serializers.CharField()
    name = serializers.CharField(required=False, allow_null=True)
    subscription_start_date = serializers.DateTimeField(required=False, allow_null=True)
    subscription_end_date = serializers.DateTimeField(required=False, allow_null=True)
    package_type = serializers.IntegerField(required=False, allow_null=True)


class CheckRegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)


class PhoneOnlySerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)


class VerifyPaymentBodySerializer(serializers.Serializer):
    transaction_id = serializers.CharField(required=True)


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for payment initiation request"""
    phone_number = serializers.CharField(required=True)
    package_id = serializers.IntegerField(required=True, min_value=1)
    amount = serializers.IntegerField(required=True, min_value=1)
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        package_id = attrs['package_id']
        amount = attrs['amount']
        expected = BiasharaPayService.get_package_price(package_id)
        if expected is None:
            valid = ', '.join(str(k) for k in sorted(settings.PACKAGE_PRICES.keys()))
            raise serializers.ValidationError({
                'package_id': f'package_id lazima iwe moja ya: {valid}'
            })
        if amount != expected:
            raise serializers.ValidationError({
                'amount': f'Kiasi lazima kiwe Tsh {expected:,} kwa package_id={package_id}'
            })
        return attrs


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
