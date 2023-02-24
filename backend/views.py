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


def get_customer_subscription(telegram_id):
    user = Customer.objects.get(telegram_id=telegram_id)

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


def get_customer_requests(telegram_id):
    user = Customer.objects.get(telegram_id=telegram_id)

    if user is None:
        return None

    requests = user.requests.all()

    return [
        serialize_request(request)
        for request in requests
    ]


def get_worker_requests(telegram_id):
    user = Worker.objects.get(telegram_id=telegram_id)

    if user is None:
        return None

    requests = user.requests.all()

    return [
        serialize_request(request)
        for request in requests
    ]


def get_user_info(telegram_id):
    worker = Worker.objects.get(telegram_id=telegram_id)
    customer = Customer.objects.get(telegram_id=telegram_id)

    if customer:
        return serialize_user(customer)

    if worker:
        return serialize_user(worker)


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


def create_request(data):
    try:
        Request.objects.create(customer=data['customer'], description=data['description'])
        return True
    except:
        return False


def subscribe(data):
    try:
        Subscription.objects.create(user=data['user'], tariff=data['tariff'])
        return True
    except:
        return False
