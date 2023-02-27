from asgiref.sync import sync_to_async
from django.db import transaction

from .models import Customer, Worker, Request, Tariff, Subscription


def serialize_request(request):
    return {
        'worker': serialize_user(request.worker)
        if request.worker else None,
        'customer': serialize_user(request.customer),
        'id': request.id,
        'title': str(request),
        'description': request.description,
        'status': request.get_status_display(),
    }


def serialize_user(user):
    return {
        'id': user.id,
        'telegram_id': user.telegram_id,
        'telegram_username': user.telegram_username,
        'name': user.name,
    }


def serialize_tariff(tariff):
    return {
            'id': tariff.id,
            'title': tariff.title,
            'price': tariff.price,
            'max_month_requests': tariff.max_month_requests,
            'max_response_time': tariff.max_response_time,
            'extra': tariff.extra,
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
        serialize_tariff(tariff)
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
def create_user(telegram_id, name, telegram_username):
    try:
        Customer.objects.create(telegram_id=telegram_id, name=name, telegram_username=telegram_username)
        return True
    except Exception as err:
        print(err)
        return False


@sync_to_async
def subscribe(telegram_id, tariff_id):
    try:
        customer = Customer.objects.get(telegram_id=telegram_id)
        Subscription.objects.create(user=customer, tariff_id=tariff_id)
        return True
    except Exception as err:
        print(err)
        return False


@sync_to_async
def get_tariff(tariff_id):
    tariff = Tariff.objects.get(id=tariff_id)
    return serialize_tariff(tariff)


@sync_to_async
def get_all_requests():
    return [
        serialize_request(request)
        for request in Request.objects.filter(status='CREATED')
    ]


@sync_to_async
def assign_worker_to_request(telegram_id, request_id):
    try:
        worker = Worker.objects.get(telegram_id=telegram_id)
        request = Request.objects.get(id=request_id)

        request.worker = worker
        request.status = 'ASSIGNED'
        request.save()
        return True
    except Exception as err:
        print(err)
        return False


@sync_to_async
def finish_request(request_id):
    try:
        request = Request.objects.get(id=request_id)
        request.status = 'DONE'
        request.save()
        return True
    except Exception as err:
        print(err)
        return False


@sync_to_async
def get_request(request_id):
    request = Request.objects.get(id=request_id)
    return serialize_request(request)
