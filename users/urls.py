from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('user/status/', views.check_and_register_user, name='check_user_status'),
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment/verify/', views.verify_payment, name='verify_payment'),
    path('payment/status/', views.check_payment_status, name='check_payment_status'),
    path('webhook/biashara/', views.biashara_webhook, name='biashara_webhook'),
]
