from .models import User


def get_user_subscription(user_id):
    user = User.objects.get(id=user_id)

    if user is None:
        return None

    subscription = user.subscriptions.first()

    return {
        'sent_requests': subscription.sent_requests,
        'tariff': {
            'title': subscription.tariff.title,
            'price': subscription.tariff.price,
            'max_month_requests': subscription.tariff.max_month_requests,
            'max_response_time': subscription.tariff.max_response_time,
            'extra': subscription.tariff.extra,
        },
        'created_at': subscription.created_at
    }


def get_user_requests(user_id):
    pass
