import textwrap

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from more_itertools import chunked

from . import start_tg_bot
from backend.views import get_user_info, get_all_requests, assign_worker_to_request, get_worker_requests, \
    finish_request, get_request


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    worker = await get_user_info(update.effective_user.id)
    if worker:
        reply_markup = [
            [InlineKeyboardButton('Взять новый запрос', callback_data='all_requests')],
            [InlineKeyboardButton('Ваши запросы', callback_data='my_requests')],
        ]
        await update.effective_chat.send_message(
            f'Здравствуйте, {worker["name"]}',
            reply_markup=InlineKeyboardMarkup(
                reply_markup
            ),
        )
        return start_tg_bot.HANDLE_FREELANCER_MENU
    else:
        await update.effective_chat.send_message(
            "Извините, но мы не можем найти вас у себя.\n\n"
            "Обратитесь к нашему администратору, если хотите стать фрилансером: https://t.me/PacmuClaB",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data="back")],
            ])
        )
        return start_tg_bot.HANDLE_USER_NOT_FOUND


async def get_requests_keyboard(requests, chunk):
    chunk_size = 5
    chunked_requests = list(chunked(requests, chunk_size))

    reply_keyboard = []

    if len(list(chunked(requests, chunk_size))) != 0:
        reply_keyboard = [[InlineKeyboardButton(request['title'], callback_data=request['id'])]
                          for request in chunked_requests[int(chunk)]]

        arrows_keyboard = []
        arrows_keyboard.append(InlineKeyboardButton('⬅️', callback_data='⬅️')) \
            if chunk != 0 else None
        arrows_keyboard.append(InlineKeyboardButton('➡️', callback_data='➡️')) \
            if chunk+1 != len(chunked_requests) else None

        reply_keyboard.append(arrows_keyboard)

    reply_keyboard.append([InlineKeyboardButton('Назад', callback_data='back')])

    return reply_keyboard


async def get_requests_text(requests, chunk):
    chunk_size = 5
    if len(list(chunked(requests, chunk_size))) != 0:
        reply_text = 'Доступные запросы:\n'

        for request in list(chunked(requests, chunk_size))[int(chunk)]:
            reply_text += textwrap.dedent(f'''
                {request['title']}
                Описание: {request['description']}
            ''')
    else:
        reply_text = 'Доступных запросов пока нет.'

    return reply_text


async def handle_freelancer_all_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == '➡️':
        context.user_data['current_chunk'] += 1
    elif query.data == '⬅️':
        context.user_data['current_chunk'] -= 1
    elif query.data == 'back':
        await query.message.delete()
        return await start(update, context)
    else:
        assigned = await assign_worker_to_request(update.effective_user.id, query.data)
        if assigned:
            await query.message.delete()
            await update.effective_chat.send_message(
                'Вы были успешно назначены для выполнения данного запроса'
            )
            return await start(update, context)
        else:
            await query.message.delete()
            await update.effective_chat.send_message(
                'Извините, произошла непредвиденная ошибка. Попробуйте снова.'
            )
            return await start(update, context)

    await query.message.delete()
    requests = await get_all_requests()
    reply_keyboard = await get_requests_keyboard(requests, context.user_data['current_chunk'])

    reply_text = await get_requests_text(requests, context.user_data['current_chunk'])

    await update.effective_chat.send_message(
        reply_text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )

    return start_tg_bot.HANDLE_FREELANCER_ALL_REQUESTS


async def get_my_requests_keyboard(requests, current_request_index):
    reply_keyboard = [
        [InlineKeyboardButton('Написать заказчику', callback_data='write_employer')],
        [InlineKeyboardButton('Сдать запрос', callback_data='finish_request')],
    ] if requests[current_request_index]['status'] != 'Готов' else []

    arrows_keyboard = []
    arrows_keyboard.append(InlineKeyboardButton('⬅️', callback_data='⬅️')) \
        if current_request_index != 0 else None
    arrows_keyboard.append(InlineKeyboardButton('➡️', callback_data='➡️')) \
        if current_request_index + 1 != len(requests) else None

    reply_keyboard.append(arrows_keyboard)

    reply_keyboard.append([InlineKeyboardButton('Назад', callback_data='back')])

    return reply_keyboard


async def get_my_requests_text(requests, current_request_index):
    current_request = requests[current_request_index]
    reply_text = textwrap.dedent(f'''
        Ваши запросы:\n
        {current_request['title']}
        Описание: {current_request['description']}
        Статус: {current_request['status']}
    ''')

    return reply_text


async def handle_freelancer_my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == '➡️':
        context.user_data['current_request_index'] += 1
    elif query.data == '⬅️':
        context.user_data['current_request_index'] -= 1
    elif query.data == 'finish_request':
        finished = await finish_request(context.user_data['current_request_id'])
        await query.message.delete()
        if finished:
            await update.effective_chat.send_message(
                'Запрос был успешно закрыт.'
            )
        else:
            await update.effective_chat.send_message(
                'Произошла непредвиденная ошибка. Попробуйте снова позже.'
            )
        return await start(update, context)
    elif query.data == 'write_employer':
        await update.effective_chat.send_message(
            'Напишите боту сообщение, которое хотите отправить заказчику.',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Назад', callback_data='back')]]
            )
        )
        return start_tg_bot.HANDLE_FREELANCER_WRITE_EMPLOYER
    elif query.data == 'back':
        await query.message.delete()
        return await start(update, context)

    requests = await get_worker_requests(update.effective_user.id)
    current_request_index = context.user_data['current_request_index']

    reply_text = await get_my_requests_text(requests, current_request_index)

    reply_keyboard = await get_my_requests_keyboard(requests, current_request_index)

    await query.message.delete()
    await update.effective_chat.send_message(
        reply_text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )
    return start_tg_bot.HANDLE_FREELANCER_MY_REQUESTS


async def handle_write_employer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.message.delete()
        return await start(update, context)
    else:
        request_id = context.user_data['current_request_id']
        request = await get_request(request_id)
        text = textwrap.dedent(f'''
            Вам сообщение от исполнителя вашего запроса: {request['title']}\n
            Описание запроса: {request['description']}\n
            Сообщение исполнителя: {update.message.text}
        ''')
        await context.bot.send_message(
            request['customer']['telegram_id'],
            text
        )
        await update.effective_user.send_message(
            'Сообщение успешно отправлено.'
        )
        return await start(update, context)


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.data == 'all_requests':
        context.user_data['current_chunk'] = 0

        requests = await get_all_requests()
        reply_keyboard = await get_requests_keyboard(requests, context.user_data['current_chunk'])

        reply_text = await get_requests_text(requests, context.user_data['current_chunk'])

        await update.callback_query.message.delete()
        await update.effective_chat.send_message(
            reply_text,
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )

        return start_tg_bot.HANDLE_FREELANCER_ALL_REQUESTS
    elif update.callback_query.data == 'my_requests':
        requests = await get_worker_requests(update.effective_user.id)
        current_request_index = 0
        context.user_data['current_request_index'] = current_request_index
        if len(requests) != 0:
            context.user_data['current_request_id'] = requests[current_request_index]['id']
            reply_text = await get_my_requests_text(requests, current_request_index)

            reply_keyboard = await get_my_requests_keyboard(requests, current_request_index)
        else:
            reply_text = 'Пока вы не взяли ни одного запроса.'
            reply_keyboard = [[InlineKeyboardButton('Назад', callback_data='back')]]

        await update.callback_query.message.delete()
        await update.effective_chat.send_message(
            reply_text,
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )

        return start_tg_bot.HANDLE_FREELANCER_MY_REQUESTS
