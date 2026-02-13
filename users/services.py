import requests
from django.conf import settings
from typing import Dict, Optional
import re


class ZenoPayService:
    """
    Service for interacting with Zeno Pay API
    """
    
    @staticmethod
    def format_phone_number(phone_number: str) -> str:
        """
        Format phone number for Zeno Pay.
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
    def initiate_payment(
        phone_number: str,
        name: str,
        amount: int,
        email: Optional[str] = None
    ) -> Dict:
        """
        Initiate a payment with Zeno Pay.
        
        Args:
            phone_number: Buyer's phone number
            name: Buyer's full name
            amount: Payment amount
            email: Optional email (defaults to phone@forexbot.com)
            
        Returns:
            Response data from Zeno API
            
        Raises:
            Exception: If payment initiation fails
        """
        # Format phone number
        formatted_phone = ZenoPayService.format_phone_number(phone_number)
        
        # Generate email if not provided
        if not email:
            email = f"{formatted_phone}@forexbot.com"
        
        # Prepare payload
        payload = {
            'create_order': '1',
            'buyer_email': email,
            'buyer_name': name,
            'buyer_phone': formatted_phone,
            'amount': str(amount),
            'account_id': settings.ZENO_ACCOUNT_ID,
            'api_key': settings.ZENO_API_KEY,
            'secret_key': settings.ZENO_SECRET_KEY,
            'currency': 'TZS',
            'payment_method': 'ussd'
        }
        
        # Make request to Zeno API
        try:
            response = requests.post(
                settings.ZENO_API_URL,
                data=payload,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
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
            response: Response from initiate_payment()
            
        Returns:
            True if payment was successful
        """
        return response.get('status') == 'success'
