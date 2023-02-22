import textwrap

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from . import start_tg_bot
from backend.models import User, Subscription


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> int:
    try:
        user = await User.objects.aget(id=user.id)
    except User.DoesNotExist:
        reply_text = textwrap.dedent('''
        Извините, но мы не смогли найти вас у себя.\n\n \
        Чтобы стать заказчиком, вам нужно оформить подписку.
        Доступные подписки:
        ''')

        reply_markup = [
            [InlineKeyboardButton("Назад", callback_data="back")],
        ]

        async for subscription in Subscription.objects.all():
            reply_text += textwrap.dedent(f'''
            {subscription.title} - {subscription.price}₽ в месяц \n
            Максимум заявок в месяц: {subscription.max_month_requests}
            Максимальное время рассмотра заявки: {subscription.max_response_time}
            Дополнительно: {subscription.extra}
            ''')

            reply_markup.append(
                [InlineKeyboardButton(subscription.title, callback_data=subscription.id)]
            )

        await update.message.reply_text(
            reply_text,
            reply_markup=InlineKeyboardMarkup(reply_markup)
        )
        return start_tg_bot.HANDLE_FREELANCER_MENU


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query.data == 'back':
        await update.callback_query.message.delete()
        return await start_tg_bot.start(update, context)