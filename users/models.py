from django.db import models
from datetime import timedelta
from django.utils import timezone


class User(models.Model):
    """
    User model for subscription management.
    Phone number is the primary identifier for authentication.
    """
    phone_number = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    package_type = models.IntegerField(null=True, blank=True, help_text="1=1 month, 2=2 months, 3=3 months")
    order_id = models.CharField(max_length=255, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - {'Active' if self.is_active else 'Inactive'}"

    def activate_subscription(self, package_type: int, order_id: str = None, transaction_id: str = None):
        """
        Activate or extend user subscription based on package type.
        
        Args:
            package_type: 1, 2, or 3 (months)
            order_id: Order ID from Zeno Pay
            transaction_id: Transaction ID from Zeno Pay
        """
        now = timezone.now()
        
        # If user already has active subscription, extend from end date
        if self.is_active and self.subscription_end_date and self.subscription_end_date > now:
            start_date = self.subscription_end_date
        else:
            start_date = now
        
        # Calculate end date based on package type
        months = package_type
        end_date = start_date + timedelta(days=months * 30)  # Approximate 30 days per month
        
        self.is_active = True
        self.subscription_start_date = start_date if not self.subscription_start_date else self.subscription_start_date
        self.subscription_end_date = end_date
        self.package_type = package_type
        
        if order_id:
            self.order_id = order_id
        if transaction_id:
            self.transaction_id = transaction_id
        
        self.save()

    def check_status(self):
        """
        Check if subscription is still active based on end date.
        Updates is_active if subscription has expired.
        """
        if self.is_active and self.subscription_end_date:
            if timezone.now() > self.subscription_end_date:
                self.is_active = False
                self.save()
        
        return {
            'exists': True,
            'is_active': self.is_active,
            'phone_number': self.phone_number,
            'name': self.name,
            'subscription_start_date': self.subscription_start_date.isoformat() if self.subscription_start_date else None,
            'subscription_end_date': self.subscription_end_date.isoformat() if self.subscription_end_date else None,
            'package_type': self.package_type,
        }
