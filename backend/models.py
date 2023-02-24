from django.db import models


class Tariff(models.Model):
    title = models.CharField('Название', max_length=50)
    price = models.PositiveSmallIntegerField('Цена')
    max_month_requests = models.PositiveSmallIntegerField('Максимум заявок в месяц')
    max_response_time = models.PositiveSmallIntegerField('Время рассмотрения заявки(в часах)')
    extra = models.CharField('Дополнительные возможности', blank=True, max_length=350)

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'

    def __str__(self):
        return self.title


class User(models.Model):
    telegram_id = models.CharField('Телеграм идентификатор', unique=True, max_length=50)
    name = models.CharField('Имя', max_length=50, null=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.name}"


class Customer(User):
    class Meta:
        verbose_name = 'Заказчик'
        verbose_name_plural = 'Заказчики'


class Worker(User):
    class Meta:
        verbose_name = 'Исполнитель'
        verbose_name_plural = 'Исполнители'


class Subscription(models.Model):
    CREATED = 'CREATED'
    ASSIGNED = 'ASSIGNED'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'
    STATUSES = [
        (CREATED, 'Создан'),
        (ASSIGNED, 'Назначен исполнитель'),
        (IN_PROGRESS, 'В работе'),
        (DONE, 'Готов'),
    ]

    user = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscriptions'
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.CASCADE,
        verbose_name='Тариф',
        related_name='subscriptions',
    )
    sent_requests = models.PositiveSmallIntegerField(
        verbose_name='Количество заявок',
        default=0,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    status = models.CharField(
        max_length=50,
        verbose_name='Статус заказа',
        choices=STATUSES,
        default=CREATED,
    )

    def has_max_requests(self):
        return self.sent_requests == self.tariff.max_month_requests

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'Подписка пользователя {self.user.name}'


class Request(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        verbose_name='Заказчик',
        related_name='requests'
    )
    worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        verbose_name='Исполнитель',
        related_name='requests',
        null=True,
        blank=True
    )
    description = models.TextField(
        verbose_name='Описание заказа'
    )

    def __str__(self):
        return f'Запрос #{self.id} от {self.customer.name}'
