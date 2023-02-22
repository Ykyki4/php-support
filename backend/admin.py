from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        if obj:
            if obj.type == 'employer':
                return 'telegram_id', 'name', 'type', 'subscription',
            else:
                return 'telegram_id', 'name', 'type',
        else:
            return 'telegram_id', 'name', 'type',


