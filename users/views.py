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
from .services import BiasharaPayService
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
        formatted_phone = BiasharaPayService.format_phone_number(phone_number)
        
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
    Initiate payment with Biashara Pay.
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
        package_type = BiasharaPayService.get_package_type(amount)
        if not package_type:
            valid_amounts = ', '.join([str(price) for price in settings.PACKAGE_PRICES.values()])
            return Response({
                'error': 'Invalid amount',
                'message': f'Amount must be one of: {valid_amounts}',
                'valid_amounts': list(settings.PACKAGE_PRICES.values())
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Format phone number
        formatted_phone = BiasharaPayService.format_phone_number(phone_number)
        
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
        
        # Generate transaction reference
        ref_trx = BiasharaPayService.generate_transaction_reference()
        
        # Initiate payment with Biashara Pay
        try:
            biashara_response = BiasharaPayService.initiate_payment(
                phone_number=formatted_phone,
                name=name,
                amount=amount,
                email=email,
                ref_trx=ref_trx
            )
            
            # Check if payment initiation was successful
            if BiasharaPayService.is_payment_successful(biashara_response):
                # Extract transaction ID and payment URL from response
                transaction_id = biashara_response.get('data', {}).get('transaction_id') or biashara_response.get('transaction_id', '')
                payment_url = biashara_response.get('data', {}).get('payment_url') or biashara_response.get('payment_url', '')
                
                # Save transaction reference and order_id to user
                user.order_id = ref_trx  # Store our ref_trx as order_id
                if transaction_id:
                    user.transaction_id = transaction_id
                user.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Payment initiated successfully',
                    'order_id': ref_trx,
                    'transaction_id': transaction_id,
                    'payment_url': payment_url,
                    'phone_number': formatted_phone,
                    'amount': amount,
                    'package_type': package_type,
                    'biashara_response': biashara_response
                }, status=status.HTTP_200_OK)
            else:
                error_message = biashara_response.get('message', 'Payment initiation failed')
                return Response({
                    'status': 'error',
                    'message': error_message,
                    'biashara_response': biashara_response
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Biashara Pay error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to initiate payment with Biashara Pay',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}")
        return Response({
            'error': 'An error occurred while initiating payment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def verify_payment(request, transaction_id):
    """
    Verify a payment transaction with Biashara Pay.
    
    GET /api/payment/verify/{transaction_id}/
    """
    try:
        if not transaction_id:
            return Response({
                'error': 'Transaction ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify payment with Biashara Pay
        try:
            verification_response = BiasharaPayService.verify_payment(transaction_id)
            
            # Check if payment was successful
            is_successful = BiasharaPayService.is_payment_successful(verification_response)
            
            # Extract payment details
            payment_data = verification_response.get('data', {})
            ref_trx = payment_data.get('ref_trx') or verification_response.get('ref_trx', '')
            amount = payment_data.get('payment_amount') or payment_data.get('amount')
            status_value = payment_data.get('status') or verification_response.get('status', '')
            
            # If payment is successful, try to find and update user
            if is_successful and ref_trx:
                try:
                    user = User.objects.get(order_id=ref_trx)
                    
                    # Get package type from amount
                    if amount:
                        package_type = BiasharaPayService.get_package_type(int(float(amount)))
                        if package_type:
                            # Activate or extend subscription
                            user.activate_subscription(
                                package_type=package_type,
                                order_id=ref_trx,
                                transaction_id=transaction_id
                            )
                            logger.info(f"Payment verified and subscription activated for {user.phone_number}")
                except User.DoesNotExist:
                    logger.warning(f"User with order_id {ref_trx} not found")
            
            return Response({
                'status': 'success' if is_successful else 'failed',
                'transaction_id': transaction_id,
                'is_payment_successful': is_successful,
                'verification_data': verification_response
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Biashara Pay verification error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to verify payment with Biashara Pay',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        return Response({
            'error': 'An error occurred while verifying payment',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def biashara_webhook(request):
    """
    Handle Biashara Pay webhook callbacks (IPN).
    
    POST /api/webhook/biashara/
    """
    try:
        # Log webhook data for debugging
        logger.info(f"Biashara Pay webhook received: {request.data}")
        
        # Get webhook data
        webhook_data = request.data
        
        # Extract payment information
        # Biashara Pay webhook format may vary, so we'll handle multiple possible formats
        ref_trx = webhook_data.get('ref_trx') or webhook_data.get('reference') or webhook_data.get('order_id', '')
        transaction_id = webhook_data.get('transaction_id') or webhook_data.get('trx_id') or webhook_data.get('id', '')
        status_value = webhook_data.get('status', '').lower()
        amount = webhook_data.get('payment_amount') or webhook_data.get('amount')
        phone_number = webhook_data.get('customer_phone') or webhook_data.get('phone') or webhook_data.get('buyer_phone', '')
        
        # Check if payment is successful
        is_successful = (
            status_value in ['success', 'successful', 'completed', 'paid'] or
            webhook_data.get('success', False) is True
        )
        
        if is_successful and ref_trx:
            # Try to find user by order_id (ref_trx)
            try:
                user = User.objects.get(order_id=ref_trx)
                
                # Get package type from amount
                if amount:
                    try:
                        amount_int = int(float(amount))
                        package_type = BiasharaPayService.get_package_type(amount_int)
                        if package_type:
                            # Activate or extend subscription
                            user.activate_subscription(
                                package_type=package_type,
                                order_id=ref_trx,
                                transaction_id=transaction_id if transaction_id else None
                            )
                            logger.info(f"Payment processed via webhook for {user.phone_number}: Package {package_type}, Order {ref_trx}")
                        else:
                            logger.warning(f"Amount {amount_int} doesn't match any package price")
                    except (ValueError, TypeError):
                        logger.error(f"Invalid amount in webhook: {amount}")
                else:
                    logger.warning(f"No amount provided in webhook for ref_trx: {ref_trx}")
                    
            except User.DoesNotExist:
                # If user not found by order_id, try by phone number
                if phone_number:
                    formatted_phone = BiasharaPayService.format_phone_number(phone_number)
                    try:
                        user = User.objects.get(phone_number=formatted_phone)
                        # Update order_id and transaction_id
                        user.order_id = ref_trx
                        if transaction_id:
                            user.transaction_id = transaction_id
                        
                        # Get package type and activate
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
                                    logger.info(f"Payment processed via webhook for {user.phone_number}: Package {package_type}")
                            except (ValueError, TypeError):
                                logger.error(f"Invalid amount in webhook: {amount}")
                        user.save()
                    except User.DoesNotExist:
                        logger.warning(f"User not found for webhook: ref_trx={ref_trx}, phone={phone_number}")
        else:
            logger.info(f"Webhook received but payment not successful: status={status_value}, ref_trx={ref_trx}")
        
        # Always return 200 OK to acknowledge receipt
        return Response('OK', status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        # Still return 200 to acknowledge receipt (Biashara Pay will retry if needed)
        return Response('Error', status=status.HTTP_200_OK)
