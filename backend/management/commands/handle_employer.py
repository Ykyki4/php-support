import textwrap

from django.conf import settings
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import ContextTypes

from . import start_tg_bot
from backend.models import User, Subscription


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> int:
    try:
        user = await User.objects.aget(id=user.id)
    except User.DoesNotExist:
        reply_text = textwrap.dedent('''
        Извините, но мы не смогли найти вас у себя.\n\n
        Чтобы стать заказчиком, вам нужно оформить подписку.
        Доступные подписки:
        ''')

        reply_markup = []

        async for subscription in Subscription.objects.all():
            reply_text += textwrap.dedent(f'''
            {subscription.title} - {subscription.price}₽ в месяц \n
            Максимум заявок в месяц: {subscription.max_month_requests}
            Максимальное время рассмотра заявки: {subscription.max_response_time}ч.\n
            ''')
            if subscription.extra:
                reply_text += f"Дополнительно: {subscription.extra}\n\n"

            reply_markup.append(
                [InlineKeyboardButton(subscription.title, callback_data=subscription.id)]
            )

        reply_markup.append(
            [InlineKeyboardButton("Назад🔙", callback_data="back")],
        )

        await update.message.reply_text(
            reply_text,
            reply_markup=InlineKeyboardMarkup(reply_markup)
        )
        return start_tg_bot.HANDLE_USER_NOT_FOUND


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query

    if query.invoice_payload != "Subscription-Payload":
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Спасибо за покупку! Теперь вам доступны возможности заказчика.")
    return