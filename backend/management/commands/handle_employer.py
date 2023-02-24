import textwrap

from django.conf import settings
from django.utils.timezone import localtime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from . import start_tg_bot
from backend.models import Subscription, Tariff, Request, Customer


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user = await Customer.objects.aget(telegram_id=update.effective_user.id)
        subscription = await user.subscriptions.select_related('tariff').afirst()

        reply_text = textwrap.dedent(f'''
                Здравствуйте, {user.name}.\n
                Ваша подписка: {subscription.tariff.title}.
                Осталось запросов: {subscription.tariff.max_month_requests - subscription.sent_requests}.
                Максимальное время ответа на запрос: {subscription.tariff.max_response_time}ч.
                Подписка продлится: {31 - (localtime() - subscription.created_at).days}д.
                ''')

        reply_keyboard = [['Сделать новый запрос'], ['Мои запросы']]

        await update.effective_chat.send_message(
            reply_text,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                input_field_placeholder="Сделать новый запрос или посмотреть существующие?"
            ),
        )

        return start_tg_bot.HANDLE_EMPLOYER_MENU

    except Customer.DoesNotExist:
        reply_text = textwrap.dedent('''
        Извините, но мы не смогли найти вас у себя.\n\n
        Чтобы стать заказчиком, вам нужно оформить подписку.
        Доступные подписки:
        ''')

        reply_markup = []

        async for tariff in Tariff.objects.all():
            reply_text += textwrap.dedent(f'''
            {tariff.title} - {tariff.price}₽ в месяц \n
            Максимум заявок в месяц: {tariff.max_month_requests}
            Максимальное время рассмотра заявки: {tariff.max_response_time}ч.\n
            ''')
            if tariff.extra:
                reply_text += f"Дополнительно: {tariff.extra}\n\n"

            reply_markup.append(
                [InlineKeyboardButton(tariff.title, callback_data=tariff.id)]
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


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user = update.message.from_user
    user = await Customer.objects.acreate(
        telegram_id=tg_user.id,
        name=tg_user.first_name,
    )
    subscription = await Subscription.objects.acreate(user=user, tariff=context.user_data['tariff'])
    await update.message.reply_text(
        f"Спасибо за покупку! {user.name}, теперь вам доступны возможности подписки {subscription.tariff.title}."
    )
    return await start(update, context)


async def handle_make_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.message.delete()
        return await start(update, context)
    else:
        user = await Customer.objects.aget(telegram_id=update.message.from_user.id)
        await Request.objects.acreate(customer=user, description=update.message.text)
        tariff = context.user_data["tariff"]
        await update.message.reply_text(
            f"Ваша заявка была создана, она будет рассмотрена в течении {tariff.max_response_time}ч. Ожидайте."
        )
        return await start(update, context)


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Сделать новый запрос":
        await update.message.reply_text(
            f"Для того чтобы сделать новый запрос, просто напишите текстовую информацию о нём боту, одним сообщением.",
            reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="back")]
                ])
            )

        return start_tg_bot.HANDLE_MAKE_REQUEST
    elif update.message.text == "Мои запросы":
        pass