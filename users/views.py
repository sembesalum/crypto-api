from datetime import timedelta

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import User
from .serializers import (
    UserStatusSerializer,
    PaymentInitiateSerializer,
    CheckRegisterSerializer,
    PhoneOnlySerializer,
    VerifyPaymentBodySerializer,
)
from .services import BiasharaPayService
from . import messages_sw as sw
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
def check_and_register_user(request):
    """
    Check or register user by WhatsApp (phone as username).

    POST /api/user/status/
    Body: {"phone_number": "255712345678"}
    """
    serializer = CheckRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'error': 'Taarifa si sahihi',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    formatted_phone = BiasharaPayService.format_phone_number(phone_number)

    try:
        user = User.objects.get(phone_number=formatted_phone)

        status_data = user.check_status()
        payload = UserStatusSerializer(status_data).data

        if user.is_active:
            if user.subscription_end_date:
                expiry = sw.format_subscription_expiry(user.subscription_end_date)
            else:
                expiry = 'bado haijabainishwa'
            payload['message'] = sw.msg_user_active(expiry)
        else:
            payload['message'] = sw.MSG_USER_INACTIVE

        return Response(payload, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        User.objects.create(
            phone_number=formatted_phone,
            name=formatted_phone,
            email=f'{formatted_phone}@forexbot.com',
        )
        user = User.objects.get(phone_number=formatted_phone)
        status_data = user.check_status()
        payload = UserStatusSerializer(status_data).data
        payload['message'] = sw.MSG_USER_CREATED
        return Response(payload, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error check/register user: {e}")
        return Response({
            'error': 'Hitilafu imetokea',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def initiate_payment(request):
    """
    Initiate payment with Biashara Pay.

    POST /api/payment/initiate/
    Body: {
        "phone_number": "255712345678",
        "package_id": 1,
        "amount": 150000,
        "name": "Jina" (optional),
        "email": "..." (optional)
    }
    """
    serializer = PaymentInitiateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'error': 'Taarifa si sahihi',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    amount = serializer.validated_data['amount']
    package_type = serializer.validated_data['package_id']

    formatted_phone = BiasharaPayService.format_phone_number(phone_number)
    name = serializer.validated_data.get('name') or formatted_phone
    name = name.strip() if isinstance(name, str) else formatted_phone
    email = serializer.validated_data.get('email') or f'{formatted_phone}@forexbot.com'

    user, created = User.objects.get_or_create(
        phone_number=formatted_phone,
        defaults={
            'name': name,
            'email': email,
        }
    )

    if not created and user.name != name:
        user.name = name
        if email:
            user.email = email
        user.save()

    ref_trx = BiasharaPayService.generate_transaction_reference()

    try:
        biashara_response = BiasharaPayService.initiate_payment(
            phone_number=formatted_phone,
            name=name,
            amount=amount,
            email=email,
            ref_trx=ref_trx
        )

        if BiasharaPayService.is_payment_successful(biashara_response):
            transaction_id = (
                biashara_response.get('data', {}).get('transaction_id')
                or biashara_response.get('transaction_id', '')
            )
            payment_url = (
                biashara_response.get('data', {}).get('payment_url')
                or biashara_response.get('payment_url', '')
            )

            user.order_id = ref_trx
            if transaction_id:
                user.transaction_id = transaction_id
            user.save()

            return Response({
                'status': 'success',
                'message': sw.msg_payment_success(amount, payment_url),
                'order_id': ref_trx,
                'transaction_id': transaction_id,
                'payment_url': payment_url,
                'phone_number': formatted_phone,
                'amount': amount,
                'package_type': package_type,
            }, status=status.HTTP_200_OK)

        error_message = biashara_response.get('message', 'Malipo hayakuanzishwa')
        return Response({
            'status': 'error',
            'message': sw.msg_payment_failed(str(error_message)),
            'biashara_response': biashara_response
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Biashara Pay error: {e}")
        return Response({
            'status': 'error',
            'message': sw.msg_payment_failed(str(e)),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def verify_payment(request):
    """
    Verify a payment transaction with Biashara Pay.

    POST /api/payment/verify/
    Body: {"transaction_id": "..."}
    """
    ser = VerifyPaymentBodySerializer(data=request.data)
    if not ser.is_valid():
        return Response({
            'error': 'transaction_id inahitajika',
            'details': ser.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    transaction_id = ser.validated_data['transaction_id']

    try:
        verification_response = BiasharaPayService.verify_payment(transaction_id)
        is_successful = BiasharaPayService.is_payment_successful(verification_response)

        payment_data = verification_response.get('data', {})
        ref_trx = payment_data.get('ref_trx') or verification_response.get('ref_trx', '')
        amount = payment_data.get('payment_amount') or payment_data.get('amount')

        if is_successful and ref_trx:
            try:
                user = User.objects.get(order_id=ref_trx)
                if amount:
                    package_type = BiasharaPayService.get_package_type(int(float(amount)))
                    if package_type:
                        user.activate_subscription(
                            package_type=package_type,
                            order_id=ref_trx,
                            transaction_id=transaction_id
                        )
                        logger.info(
                            f'Payment verified and subscription activated for {user.phone_number}'
                        )
            except User.DoesNotExist:
                logger.warning(f'User with order_id {ref_trx} not found')

        return Response({
            'status': 'success' if is_successful else 'failed',
            'transaction_id': transaction_id,
            'is_payment_successful': is_successful,
            'verification_data': verification_response
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'Biashara Pay verification error: {e}')
        return Response({
            'status': 'error',
            'message': 'Imeshindikana kuthibitisha malipo',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def check_payment_status(request):
    """
    Check if user completed a payment within the last 6 hours.

    POST /api/payment/status/
    Body: {"phone_number": "255712345678"}
    """
    ser = PhoneOnlySerializer(data=request.data)
    if not ser.is_valid():
        return Response({
            'error': 'Taarifa si sahihi',
            'details': ser.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    formatted_phone = BiasharaPayService.format_phone_number(
        ser.validated_data['phone_number']
    )

    try:
        user = User.objects.get(phone_number=formatted_phone)
    except User.DoesNotExist:
        return Response({
            'exists': False,
            'paid_within_6_hours': False,
            'message': sw.MSG_NO_RECENT_PAYMENT,
        }, status=status.HTTP_200_OK)

    cutoff = timezone.now() - timedelta(hours=6)
    paid = (
        user.last_successful_payment_at is not None
        and user.last_successful_payment_at >= cutoff
    )

    if paid:
        msg = sw.MSG_PAYMENT_COMPLETED_RECENT
    else:
        msg = sw.MSG_NO_RECENT_PAYMENT

    return Response({
        'exists': True,
        'paid_within_6_hours': paid,
        'message': msg,
        'phone_number': formatted_phone,
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def biashara_webhook(request):
    """
    Handle Biashara Pay webhook callbacks (IPN).

    POST /api/webhook/biashara/
    """
    try:
        logger.info(f'Biashara Pay webhook received: {request.data}')

        webhook_data = request.data

        ref_trx = (
            webhook_data.get('ref_trx')
            or webhook_data.get('reference')
            or webhook_data.get('order_id', '')
        )
        transaction_id = (
            webhook_data.get('transaction_id')
            or webhook_data.get('trx_id')
            or webhook_data.get('id', '')
        )
        status_value = str(webhook_data.get('status', '')).lower()
        amount = webhook_data.get('payment_amount') or webhook_data.get('amount')
        phone_number = (
            webhook_data.get('customer_phone')
            or webhook_data.get('phone')
            or webhook_data.get('buyer_phone', '')
        )

        is_successful = (
            status_value in ['success', 'successful', 'completed', 'paid']
            or webhook_data.get('success', False) is True
        )

        if is_successful and ref_trx:
            try:
                user = User.objects.get(order_id=ref_trx)

                if amount:
                    try:
                        amount_int = int(float(amount))
                        package_type = BiasharaPayService.get_package_type(amount_int)
                        if package_type:
                            user.activate_subscription(
                                package_type=package_type,
                                order_id=ref_trx,
                                transaction_id=transaction_id if transaction_id else None
                            )
                            logger.info(
                                f'Payment processed via webhook for {user.phone_number}: '
                                f'Package {package_type}, Order {ref_trx}'
                            )
                        else:
                            logger.warning(
                                f'Amount {amount_int} doesn\'t match any package price'
                            )
                    except (ValueError, TypeError):
                        logger.error(f'Invalid amount in webhook: {amount}')
                else:
                    logger.warning(f'No amount provided in webhook for ref_trx: {ref_trx}')

            except User.DoesNotExist:
                if phone_number:
                    formatted_phone = BiasharaPayService.format_phone_number(phone_number)
                    try:
                        user = User.objects.get(phone_number=formatted_phone)
                        user.order_id = ref_trx
                        if transaction_id:
                            user.transaction_id = transaction_id

                        if amount:
                            try:
                                amount_int = int(float(amount))
                                package_type = BiasharaPayService.get_package_type(amount_int)
                                if package_type:
                                    user.activate_subscription(
                                        package_type=package_type,
                                        order_id=ref_trx,
                                        transaction_id=transaction_id if transaction_id else None
                                    )
                                    logger.info(
                                        f'Payment processed via webhook for {user.phone_number}: '
                                        f'Package {package_type}'
                                    )
                            except (ValueError, TypeError):
                                logger.error(f'Invalid amount in webhook: {amount}')
                        user.save()
                    except User.DoesNotExist:
                        logger.warning(
                            f'User not found for webhook: ref_trx={ref_trx}, phone={phone_number}'
                        )
        else:
            logger.info(
                f'Webhook received but payment not successful: status={status_value}, '
                f'ref_trx={ref_trx}'
            )

        return Response('OK', status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'Webhook error: {e}')
        return Response('Error', status=status.HTTP_200_OK)
