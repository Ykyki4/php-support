import logging

from django.conf import settings
from django.core.management import BaseCommand
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardMarkup, InlineKeyboardButton, \
    LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CallbackQueryHandler, PreCheckoutQueryHandler,
)

from . import handle_freelancer, handle_employer
from ...models import Subscription, Tariff

USER_TYPE, HANDLE_USER_NOT_FOUND, WAIT_PAYMENT, HANDLE_EMPLOYER_MENU = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Заказчик", "Фрилансер"]]

    await update.effective_chat.send_message(
        "Здравствуй! Я бот PHPSupport, связывающий заказчиков с фрилансерами.\n\n"
        "Вы заказчик или фрилансер?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Заказчик или фрилансер?"
        ),
    )

    return USER_TYPE


async def user_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user

    if update.message.text == "Заказчик":
        return await handle_employer.start(update, context)
    elif update.message.text == "Фрилансер":
        return await handle_freelancer.start(update, context, user)


async def handle_user_not_found(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query.data == 'back':
        await update.callback_query.message.delete()
        return await start(update, context)
    else:
        tariff = await Tariff.objects.aget(id=update.callback_query.data)
        context.user_data['tariff_id'] = tariff.id

        description = f"Покупка подписки {tariff.title} на месяц."

        payload = "Subscription-Payload"

        currency = "RUB"

        prices = [LabeledPrice("Test", tariff.price * 100)]

        await update.effective_chat.send_invoice(
            tariff.title, description, payload, settings.TG_PAYMENT_PROVIDER_TOKEN, currency, prices
        )

        return WAIT_PAYMENT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Пока-пока!", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


class Command(BaseCommand):
    help = "Start telegram bot"

    def handle(self, *args, **options):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
        )

        application = Application.builder().token(settings.TG_BOT_TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                USER_TYPE: [
                    MessageHandler(filters.Regex("^(Заказчик|Фрилансер)$"), user_type)
                ],
                HANDLE_USER_NOT_FOUND: [
                    CallbackQueryHandler(handle_user_not_found),
                    MessageHandler(filters.TEXT, handle_user_not_found)
                ],
                WAIT_PAYMENT: [
                    PreCheckoutQueryHandler(handle_employer.precheckout_callback),
                    MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_employer.successful_payment_callback)
                ],
                HANDLE_EMPLOYER_MENU: [
                    MessageHandler(filters.TEXT, handle_employer.handle_menu),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            per_chat=False,
        )

        application.add_handler(conv_handler)

        application.run_polling()