from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import User
from .serializers import (
    UserStatusSerializer,
    PaymentInitiateSerializer,
    PaymentResponseSerializer,
    WebhookSerializer
)
from .services import ZenoPayService
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def check_user_status(request, phone_number):
    """
    Check if user exists and their subscription status.
    
    GET /api/user/status/{phone_number}/
    """
    try:
        # Format phone number
        formatted_phone = ZenoPayService.format_phone_number(phone_number)
        
        # Get user
        try:
            user = User.objects.get(phone_number=formatted_phone)
            status_data = user.check_status()
            
            serializer = UserStatusSerializer(status_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'exists': False,
                'is_active': False,
                'phone_number': formatted_phone,
                'message': 'User not found'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error checking user status: {str(e)}")
        return Response({
            'error': 'An error occurred while checking user status',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def initiate_payment(request):
    """
    Initiate payment with Zeno Pay.
    Creates user automatically if they don't exist.
    
    POST /api/payment/initiate/
    Body: {
        "phone_number": "255712345678",
        "amount": 150000,
        "name": "John Doe",
        "email": "john@example.com" (optional)
    }
    """
    try:
        # Validate request data
        serializer = PaymentInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid request data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        phone_number = serializer.validated_data['phone_number']
        amount = serializer.validated_data['amount']
        name = serializer.validated_data['name']
        email = serializer.validated_data.get('email')
        
        # Validate amount matches a package price
        package_type = ZenoPayService.get_package_type(amount)
        if not package_type:
            valid_amounts = ', '.join([str(price) for price in settings.PACKAGE_PRICES.values()])
            return Response({
                'error': 'Invalid amount',
                'message': f'Amount must be one of: {valid_amounts}',
                'valid_amounts': list(settings.PACKAGE_PRICES.values())
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Format phone number
        formatted_phone = ZenoPayService.format_phone_number(phone_number)
        
        # Get or create user
        user, created = User.objects.get_or_create(
            phone_number=formatted_phone,
            defaults={
                'name': name,
                'email': email or f"{formatted_phone}@forexbot.com"
            }
        )
        
        # Update user name if it changed
        if not created and user.name != name:
            user.name = name
            if email:
                user.email = email
            user.save()
        
        # Initiate payment with Zeno Pay
        try:
            zeno_response = ZenoPayService.initiate_payment(
                phone_number=formatted_phone,
                name=name,
                amount=amount,
                email=email
            )
            
            # Check if payment initiation was successful
            if ZenoPayService.is_payment_successful(zeno_response):
                order_id = zeno_response.get('order_id', '')
                payment_url = zeno_response.get('payment_url', '')
                
                # Save order_id to user (temporarily, will be confirmed via webhook)
                user.order_id = order_id
                user.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Payment initiated successfully',
                    'order_id': order_id,
                    'payment_url': payment_url,
                    'phone_number': formatted_phone,
                    'amount': amount,
                    'package_type': package_type
                }, status=status.HTTP_200_OK)
            else:
                error_message = zeno_response.get('message', 'Payment initiation failed')
                return Response({
                    'status': 'error',
                    'message': error_message,
                    'zeno_response': zeno_response
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Zeno Pay error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to initiate payment with Zeno Pay',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}")
        return Response({
            'error': 'An error occurred while initiating payment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def zeno_webhook(request):
    """
    Handle Zeno Pay webhook callbacks.
    
    POST /api/webhook/zeno/
    """
    try:
        # Validate webhook data
        serializer = WebhookSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid webhook data: {serializer.errors}")
            return Response('Invalid data', status=status.HTTP_400_BAD_REQUEST)
        
        webhook_data = serializer.validated_data
        status_value = webhook_data.get('status')
        buyer_phone = webhook_data.get('buyer_phone')
        amount_str = webhook_data.get('amount')
        order_id = webhook_data.get('order_id', '')
        transaction_id = webhook_data.get('transaction_id', '')
        
        # Format phone number
        formatted_phone = ZenoPayService.format_phone_number(buyer_phone)
        
        # Convert amount to integer
        try:
            amount = int(amount_str)
        except (ValueError, TypeError):
            logger.error(f"Invalid amount in webhook: {amount_str}")
            return Response('Invalid amount', status=status.HTTP_400_BAD_REQUEST)
        
        # Process successful payment
        if status_value == 'success':
            # Get package type from amount
            package_type = ZenoPayService.get_package_type(amount)
            if not package_type:
                logger.warning(f"Amount {amount} doesn't match any package price")
                return Response('Invalid amount', status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create user
            try:
                user = User.objects.get(phone_number=formatted_phone)
            except User.DoesNotExist:
                logger.warning(f"User {formatted_phone} not found for webhook")
                return Response('User not found', status=status.HTTP_400_BAD_REQUEST)
            
            # Activate or extend subscription
            user.activate_subscription(
                package_type=package_type,
                order_id=order_id if order_id else None,
                transaction_id=transaction_id if transaction_id else None
            )
            
            logger.info(f"Payment processed for {formatted_phone}: Package {package_type}, Order {order_id}")
            
        # Always return 200 OK to acknowledge receipt
        return Response('OK', status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        # Still return 200 to acknowledge receipt (Zeno will retry if needed)
        return Response('Error', status=status.HTTP_200_OK)
