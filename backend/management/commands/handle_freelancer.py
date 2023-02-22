from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from backend.models import User
from . import start_tg_bot


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> int:
    try:
        user = await User.objects.aget(id=user.id)
    except User.DoesNotExist:
        await update.message.reply_text(
            "Извините, но мы не можем найти вас у себя.\n\n"
            "Обратитесь к нашему администратору, если хотите стать фрилансером: https://t.me/PacmuClaB",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data="back")],
            ])
        )
        return start_tg_bot.HANDLE_FREELANCER_MENU


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query.data == 'back':
        await update.callback_query.message.delete()
        return await start_tg_bot.start(update, context)
