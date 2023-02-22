from django.db import models

USER_TYPE_CHOICES = [
    ('employer', 'Заказчик'),
    ('freelancer', 'Фрилансер')
]


class Subscription(models.Model):
    title = models.CharField('Название', max_length=50)
    price = models.PositiveSmallIntegerField('Цена')
    max_month_requests = models.PositiveSmallIntegerField('Максимум заявок в месяц')
    max_response_time = models.PositiveSmallIntegerField('Время рассмотрения заявки(в часах)')
    extra = models.CharField('Дополнительные возможности', max_length=350)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return self.title


class User(models.Model):
    telegram_id = models.CharField('Телеграм идентификатор', max_length=50)
    name = models.CharField('Имя', max_length=50, null=True)
    type = models.CharField('Тип пользователя', choices=USER_TYPE_CHOICES, max_length=20)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        verbose_name='Подписка',
        related_name='users',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.name} - {self.get_type_display()}"
