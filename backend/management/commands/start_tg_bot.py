import logging

from django.conf import settings
from django.core.management import BaseCommand
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CallbackQueryHandler,
)

from . import handle_freelancer, handle_employer
from ...models import User

USER_TYPE, HANDLE_EMPLOYER_MENU, HANDLE_FREELANCER_MENU = range(3)


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
        return await handle_employer.start(update, context, user)
    elif update.message.text == "Фрилансер":
        return await handle_freelancer.start(update, context, user)


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
                USER_TYPE: [MessageHandler(filters.Regex("^(Заказчик|Фрилансер)$"), user_type)],
                HANDLE_EMPLOYER_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_employer.handle_menu)],
                HANDLE_FREELANCER_MENU: [
                    CallbackQueryHandler(handle_freelancer.handle_menu),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_freelancer.handle_menu)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        application.add_handler(conv_handler)

        application.run_polling()