"""User-facing Swahili messages for API responses."""
from django.utils import timezone


def format_subscription_expiry(dt):
    if not dt:
        return ''
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    local = timezone.localtime(dt)
    return local.strftime('%d/%m/%Y %H:%M')


def msg_user_active(expiry_formatted: str) -> str:
    return (
        f'Karibu tena, account yako iko active hadi {expiry_formatted}.'
    )


MSG_USER_INACTIVE = (
    'Karibu tena, account yako haiko active. Tafadhali lipia kuendelea kupata huduma zetu.'
)

MSG_USER_CREATED = (
    'Karibu sana, account yako imetengenezwa endelea kufurahia huduma zetu.'
)


def msg_payment_success(amount: int, payment_url: str) -> str:
    return (
        f'Gusa link hapa chini kufanya malipo yako ya Tsh {amount:,} {payment_url}'
    )


def msg_payment_failed(reason: str) -> str:
    return f'Malipo yameshindikana, {reason}'


MSG_PAYMENT_COMPLETED_RECENT = (
    'Hongera malipo yamekamilika sasa unaweza kupata signal zetu kila siku.'
)

MSG_NO_RECENT_PAYMENT = (
    'Pole, hakuna malipo yaliyofanyika kwenye account yako.'
)
