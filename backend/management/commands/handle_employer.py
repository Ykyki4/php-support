import textwrap

from django.utils.timezone import localtime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from . import start_tg_bot
from backend.views import get_customer_subscription, get_tariffs, create_request, get_customer_requests, \
        create_user, subscribe


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    subscription = await get_customer_subscription(update.effective_user.id)
    if subscription:
        context.user_data['subscription'] = subscription

        reply_text = textwrap.dedent(f'''
                Здравствуйте, {update.effective_user.first_name}.\n
                Ваша подписка: {subscription['tariff']['title']}.
                Осталось запросов: {subscription['tariff']['max_month_requests'] - subscription['sent_requests']}.
                Максимальное время ответа на запрос: {subscription['tariff']['max_response_time']}ч.
                Подписка продлится: {31 - (localtime() - subscription['created_at']).days}д.
                ''')

        reply_keyboard = [[InlineKeyboardButton('Мои запросы', callback_data="all_requests")]]

        if subscription['has_max_requests']:
            reply_text += "Извините, вы достигли максимального количества заявок в месяц по вашей подписке."
        else:
            reply_keyboard.append([InlineKeyboardButton('Сделать новый запрос', callback_data="new_request")])

        await update.effective_chat.send_message(
            reply_text,
            reply_markup=InlineKeyboardMarkup(
                reply_keyboard
            ),
        )

        return start_tg_bot.HANDLE_EMPLOYER_MENU
    else:
        reply_text = textwrap.dedent('''
        Извините, но мы не смогли найти вас у себя.\n\n
        Чтобы стать заказчиком, вам нужно оформить подписку.
        Доступные подписки:
        ''')

        reply_markup = []

        for tariff in await get_tariffs():
            reply_text += textwrap.dedent(f'''
            {tariff['title']} - {tariff['price']}₽ в месяц \n
            Максимум заявок в месяц: {tariff['max_month_requests']}
            Максимальное время рассмотра заявки: {tariff['max_response_time']}ч.\n
            ''')
            if tariff['extra']:
                reply_text += f"Дополнительно: {tariff['extra']}\n\n"

            reply_markup.append(
                [InlineKeyboardButton(tariff['title'], callback_data=tariff['id'])]
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
    tariff_id = context.user_data['tariff_id']
    tg_user = update.effective_user

    await create_user(tg_user.id, tg_user.first_name)
    created = await subscribe(tg_user.id, tariff_id)
    if created:
        await update.message.reply_text(
            f"Спасибо за покупку!"
        )
        return await start(update, context)
    else:
        await update.message.reply_text(
            f"Извините, произошла непредвиденная ошибка. Попробуйте снова."
        )
        return await start_tg_bot.start(update, context)


async def handle_make_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.message.delete()
        return await start(update, context)
    else:
        created = await create_request(update.effective_user.id, update.message.text)

        if created:
            subscription = context.user_data['subscription']
            await update.effective_chat.send_message(
                "Ваша заявка была создана, она будет рассмотрена в течении"
                f" {subscription['tariff']['max_response_time']}ч. Ожидайте."
            )
            return await start(update, context)
        else:
            await update.effective_chat.send_message(
                "Извините, произошла непредвиденная ошибка, или вы достигли максимального количества запросов."
                "Попробуйте снова позже."
            )
            return await start(update, context)


async def handle_show_all_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query.data == "back":
        await update.callback_query.message.delete()
        return await start(update, context)


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query.data == 'new_request':
        await update.callback_query.message.delete()
        await update.effective_chat.send_message(
            f"Для того чтобы сделать новый запрос, просто напишите текстовую информацию о нём боту, одним сообщением.",
            reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="back")]
                ])
            )

        return start_tg_bot.HANDLE_MAKE_REQUEST

    elif update.callback_query.data == 'all_requests':
        reply_text = "Ваши запросы:\n"

        for request in await get_customer_requests(update.effective_user.id):
            reply_text += textwrap.dedent(f'''
            Описание запроса: {request['description']}
            Статус запроса: {request['status']}
            ''')

        await update.callback_query.message.delete()
        await update.effective_chat.send_message(
            reply_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data="back")]
            ])
        )
        return start_tg_bot.HANDLE_SHOW_ALL_EMPLOYER_REQUESTS

