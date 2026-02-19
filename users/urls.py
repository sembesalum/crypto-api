from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('user/status/<str:phone_number>/', views.check_user_status, name='check_user_status'),
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment/verify/<str:transaction_id>/', views.verify_payment, name='verify_payment'),
    path('webhook/biashara/', views.biashara_webhook, name='biashara_webhook'),
]
