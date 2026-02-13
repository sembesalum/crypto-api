from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'name', 'is_active', 'package_type', 'subscription_start_date', 'subscription_end_date', 'created_at']
    list_filter = ['is_active', 'package_type', 'created_at']
    search_fields = ['phone_number', 'name', 'email']
    readonly_fields = ['created_at', 'updated_at']
