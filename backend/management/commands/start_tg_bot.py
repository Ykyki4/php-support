import logging

from django.conf import settings
from django.core.management import BaseCommand
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CallbackQueryHandler, PreCheckoutQueryHandler,
)

from . import handle_freelancer, handle_employer
from backend.views import get_tariff

USER_TYPE, HANDLE_USER_NOT_FOUND, WAIT_PAYMENT, HANDLE_EMPLOYER_MENU, \
    HANDLE_MAKE_REQUEST, HANDLE_SHOW_EMPLOYER_REQUESTS, HANDLE_FREELANCER_MENU, HANDLE_FREELANCER_ALL_REQUESTS, \
    HANDLE_FREELANCER_MY_REQUESTS, HANDLE_FREELANCER_WRITE_EMPLOYER, HANDLE_EMPLOYER_WRITE_FREELANCER = range(11)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Заказчик', 'Фрилансер']]

    await update.effective_chat.send_message(
        'Здравствуй! Я бот PHPSupport, связывающий заказчиков с фрилансерами.\n\n'
        'Вы заказчик или фрилансер?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Заказчик или фрилансер?'
        ),
    )

    return USER_TYPE


async def user_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == 'Заказчик':
        return await handle_employer.start(update, context)
    elif update.message.text == 'Фрилансер':
        return await handle_freelancer.start(update, context)


async def handle_user_not_found(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query.data == 'back':
        await update.callback_query.message.delete()
        return await start(update, context)
    else:
        tariff_id = update.callback_query.data
        context.user_data['tariff_id'] = tariff_id
        tariff = await get_tariff(tariff_id)

        description = f'Покупка подписки {tariff["title"]} на месяц.'

        payload = 'Subscription-Payload'

        currency = 'RUB'

        prices = [LabeledPrice('Test', tariff['price'] * 100)]

        await update.effective_chat.send_invoice(
            tariff['title'], description, payload, settings.TG_PAYMENT_PROVIDER_TOKEN, currency, prices
        )

        return WAIT_PAYMENT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Пока-пока!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


class Command(BaseCommand):
    help = 'Start telegram bot'

    def handle(self, *args, **options):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
        )

        application = Application.builder().token(settings.TG_BOT_TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                USER_TYPE: [
                    MessageHandler(filters.Regex('^(Заказчик|Фрилансер)$'), user_type)
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
                    CallbackQueryHandler(handle_employer.handle_menu),
                ],
                HANDLE_MAKE_REQUEST: [
                    CallbackQueryHandler(handle_employer.handle_make_request),
                    MessageHandler(filters.TEXT, handle_employer.handle_make_request),
                ],
                HANDLE_SHOW_EMPLOYER_REQUESTS: [
                    CallbackQueryHandler(handle_employer.handle_show_all_requests)
                ],
                HANDLE_FREELANCER_MENU: [
                    CallbackQueryHandler(handle_freelancer.handle_menu),
                ],
                HANDLE_FREELANCER_ALL_REQUESTS: [
                    CallbackQueryHandler(handle_freelancer.handle_freelancer_all_requests)
                ],
                HANDLE_FREELANCER_MY_REQUESTS: [
                    CallbackQueryHandler(handle_freelancer.handle_freelancer_my_requests)
                ],
                HANDLE_FREELANCER_WRITE_EMPLOYER: [
                    CallbackQueryHandler(handle_freelancer.handle_write_employer),
                    MessageHandler(filters.TEXT, handle_freelancer.handle_write_employer)
                ],
                HANDLE_EMPLOYER_WRITE_FREELANCER: [
                    CallbackQueryHandler(handle_employer.handle_write_freelancer),
                    MessageHandler(filters.TEXT, handle_employer.handle_write_freelancer)
                ]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            per_chat=False,
        )

        application.add_handler(conv_handler)

        application.run_polling()
        