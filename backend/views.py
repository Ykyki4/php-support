from asgiref.sync import sync_to_async
from django.db import transaction

from .models import Customer, Worker, Request, Tariff, Subscription


def serialize_request(request):
    return {
        'worker': {
            'id': request.worker.id,
            'telegram_id': request.worker.telegram_id,
            'name': request.worker.name,
        } if request.worker else None,
        'customer': {
            'id': request.customer.id,
            'telegram_id': request.customer.telegram_id,
            'name': request.customer.name
        },
        'description': request.description,
        'status': dict(Request.STATUSES).get(request.status),
    }


def serialize_user(user):
    return {
        'id': user.id,
        'telegram_id': user.telegram_id,
        'name': user.name,
    }


@sync_to_async
def get_customer_subscription(telegram_id):
    try:
        user = Customer.objects.get(telegram_id=telegram_id)
    except Customer.DoesNotExist:
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
        'created_at': subscription.created_at,
        'has_max_requests': subscription.has_max_requests()
    }


@sync_to_async
def get_customer_requests(telegram_id):
    try:
        user = Customer.objects.get(telegram_id=telegram_id)
    except Customer.DoesNotExist:
        return None

    requests = user.requests.all()

    return [
        serialize_request(request)
        for request in requests
    ]


@sync_to_async
def get_worker_requests(telegram_id):
    try:
        user = Worker.objects.get(telegram_id=telegram_id)
    except Worker.DoesNotExist:
        return None

    requests = user.requests.all()

    return [
        serialize_request(request)
        for request in requests
    ]


@sync_to_async
def get_user_info(telegram_id):
    try:
        worker = Worker.objects.get(telegram_id=telegram_id)
        return serialize_user(worker)
    except Worker.DoesNotExist:
        pass

    try:
        customer = Customer.objects.get(telegram_id=telegram_id)
        return serialize_user(customer)
    except Customer.DoesNotExist:
        pass


@sync_to_async
def get_tariffs():
    return [
        {
            'id': tariff.id,
            'title': tariff.title,
            'price': tariff.price,
            'max_month_requests': tariff.max_month_requests,
            'max_response_time': tariff.max_response_time,
            'extra': tariff.extra,
        }
        for tariff in Tariff.objects.all()
    ]


@sync_to_async
@transaction.atomic()
def create_request(telegram_id, description):
    try:
        customer = Customer.objects.get(telegram_id=telegram_id)
        subscription = customer.subscriptions.first()
        if subscription.has_max_requests():
            return False

        subscription.sent_requests += 1
        subscription.save()
        Request.objects.create(customer=customer, description=description)
        return True
    except Exception as err:
        print(err)
        return False


@sync_to_async
def subscribe(data):
    try:
        customer = Customer.objects.get(telegram_id=data['customer'])
        Subscription.objects.create(user=customer, tariff_id=data['tariff'])
        return True
    except Exception as err:
        print(err)
        return False
