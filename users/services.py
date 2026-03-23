import requests
from django.conf import settings
from typing import Dict, Optional
import re
import uuid


class BiasharaPayService:
    """
    Service for interacting with Biashara Pay API
    Reference: https://biasharapay.com/api-docs
    """
    
    @staticmethod
    def format_phone_number(phone_number: str) -> str:
        """
        Format phone number.
        Removes spaces, dashes, and ensures country code format (255 for Tanzania).
        
        Args:
            phone_number: Raw phone number
            
        Returns:
            Formatted phone number with country code
        """
        # Remove all non-digit characters
        cleaned = re.sub(r'[^0-9]', '', phone_number)
        
        # If starts with 0, replace with country code (255 for Tanzania)
        if cleaned.startswith('0'):
            cleaned = '255' + cleaned[1:]
        
        # If doesn't start with country code, add it
        if not cleaned.startswith('255'):
            cleaned = '255' + cleaned
        
        return cleaned
    
    @staticmethod
    def get_package_type(amount: int) -> Optional[int]:
        """
        Get package type based on amount.
        
        Args:
            amount: Payment amount
            
        Returns:
            Package type (1, 2, or 3) or None if amount doesn't match
        """
        for package_type, price in settings.PACKAGE_PRICES.items():
            if amount == price:
                return package_type
        return None

    @staticmethod
    def get_package_price(package_id: int) -> Optional[int]:
        """Return TZS price for package_id (1, 2, or 3) or None."""
        return settings.PACKAGE_PRICES.get(package_id)
    
    @staticmethod
    def generate_transaction_reference() -> str:
        """
        Generate a unique transaction reference.
        
        Returns:
            Unique transaction reference string
        """
        return f"TXN_{uuid.uuid4().hex[:12].upper()}"
    
    @staticmethod
    def initiate_payment(
        phone_number: str,
        name: str,
        amount: int,
        email: Optional[str] = None,
        ref_trx: Optional[str] = None
    ) -> Dict:
        """
        Initiate a payment with Biashara Pay.
        
        Args:
            phone_number: Buyer's phone number
            name: Buyer's full name
            amount: Payment amount
            email: Optional email
            ref_trx: Optional transaction reference (generated if not provided)
            
        Returns:
            Response data from Biashara Pay API
            
        Raises:
            Exception: If payment initiation fails
        """
        # Format phone number
        formatted_phone = BiasharaPayService.format_phone_number(phone_number)
        
        # Generate transaction reference if not provided
        if not ref_trx:
            ref_trx = BiasharaPayService.generate_transaction_reference()
        
        # Generate email if not provided
        if not email:
            email = f"{formatted_phone}@forexbot.com"
        
        # Get base URL from settings or use default
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        # Ensure base_url doesn't end with slash
        base_url = base_url.rstrip('/')
        
        # Prepare payload with properly formatted URLs
        payload = {
            'payment_amount': float(amount),
            'currency_code': 'TZS',
            'ref_trx': ref_trx,
            'description': f'Subscription payment for {name}',
            'success_redirect': f'{base_url}/api/payment/success',
            'failure_url': f'{base_url}/api/payment/failed',
            'cancel_redirect': f'{base_url}/api/payment/cancelled',
            'ipn_url': f'{base_url}/api/webhook/biashara/',
            'customer_name': name,
            'customer_email': email
        }
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'X-Environment': settings.BIASHARA_ENVIRONMENT,
            'X-Merchant-Key': settings.BIASHARA_MERCHANT_KEY,
            'X-API-Key': settings.BIASHARA_API_KEY
        }
        
        # Make request to Biashara Pay API
        try:
            response = requests.post(
                f"{settings.BIASHARA_API_URL}/initiate-payment",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Check HTTP status
            if response.status_code not in [200, 201]:
                raise Exception(f"HTTP Error {response.status_code}: {response.text}")
            
            # Parse JSON response
            data = response.json()
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response: {str(e)}")
    
    @staticmethod
    def verify_payment(transaction_id: str) -> Dict:
        """
        Verify a payment transaction with Biashara Pay.
        
        Args:
            transaction_id: Transaction ID from Biashara Pay
            
        Returns:
            Response data from Biashara Pay API
            
        Raises:
            Exception: If payment verification fails
        """
        # Prepare headers
        headers = {
            'Accept': 'application/json',
            'X-Environment': settings.BIASHARA_ENVIRONMENT,
            'X-Merchant-Key': settings.BIASHARA_MERCHANT_KEY,
            'X-API-Key': settings.BIASHARA_API_KEY
        }
        
        # Make request to Biashara Pay API
        try:
            response = requests.get(
                f"{settings.BIASHARA_API_URL}/verify-payment/{transaction_id}",
                headers=headers,
                timeout=30
            )
            
            # Check HTTP status
            if response.status_code != 200:
                raise Exception(f"HTTP Error {response.status_code}: {response.text}")
            
            # Parse JSON response
            data = response.json()
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response: {str(e)}")
    
    @staticmethod
    def is_payment_successful(response: Dict) -> bool:
        """
        Check if payment was successful based on response.
        
        Args:
            response: Response from initiate_payment() or verify_payment()
            
        Returns:
            True if payment was successful
        """
        return response.get('success', False) is True
