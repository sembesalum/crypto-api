from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('user/status/<str:phone_number>/', views.check_user_status, name='check_user_status'),
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('webhook/zeno/', views.zeno_webhook, name='zeno_webhook'),
]
