import datetime

from aiogram import Router, types, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from admin_panel.main_menu import admin, admin_panel
from utils import models as db

router = Router()


class requests(StatesGroup):
    comment = State()


def categories_kb(offset, request):
    buttons = []
    requests_count = request['total_count']
    request_id = request['id']
    prev_id = (offset - 1) % requests_count
    next_id = (offset + 1) % requests_count
    if requests_count == 1:
        buttons.append([
            types.InlineKeyboardButton(text='⬅️⬅️⬅️', callback_data="None"),
            types.InlineKeyboardButton(text='1/1', callback_data="None"),
            types.InlineKeyboardButton(text='➡️➡️➡️', callback_data="None")
        ])
    else:
        buttons.append([
            types.InlineKeyboardButton(text='⬅️⬅️⬅️',
                                       callback_data=f"requests_moderation_{prev_id}"),
            types.InlineKeyboardButton(text=f'{offset + 1}/{requests_count}', callback_data="None"),
            types.InlineKeyboardButton(text='➡️➡️➡️',
                                       callback_data=f"requests_moderation_{next_id}")
        ])
    buttons.append(
        [types.InlineKeyboardButton(text="Отказать без причины", callback_data=f"deny_without_{request_id}")])
    buttons.append([types.InlineKeyboardButton(text="Отказать c причиной", callback_data=f"deny_with_{request_id}")])
    buttons.append([types.InlineKeyboardButton(text="Одобрить", callback_data=f"allow_{request_id}")])
    buttons.append([types.InlineKeyboardButton(text="Назад", callback_data="admin_panel")])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def cansel_kb():
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='cansel')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data.startswith('requests_moderation_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    offset = int(callback.data.split('_')[2])
    await state.update_data({'requests_offset': offset})
    await send_request_message(callback, bot, state)


async def send_request_message(callback, bot, state):
    data = await state.get_data()
    requests = db.get_requests(status='active', offset=data['requests_offset'])

    if not requests or not requests.get('total_count'):
        await callback.answer('Не активных заявок', show_alert=True)
        await admin_panel(callback.message, state, bot)
        return

    text = f"Тип: {requests['seller_type']}\nНазвание: {requests['name']}\nФИО: {requests['fio']}\nНомер: {requests['phone']}\nИнн поставщика: `{requests['inn']}`\n"
    offset = data.get('requests_offset', 0)

    if requests['document_type'] == 'document':
        msg = await bot.send_document(chat_id=callback.message.chat.id, document=requests['file_id'], caption=text,
                                      reply_markup=categories_kb(offset, requests), parse_mode="MARKDOWN")
    else:
        msg = await bot.send_photo(chat_id=callback.message.chat.id, photo=requests['file_id'], caption=text,
                                   reply_markup=categories_kb(offset, requests), parse_mode="MARKDOWN")

    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])

    await state.update_data({'msg_id': msg.message_id})


@router.callback_query(F.data.startswith('deny_without_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request = callback.data.split('_')[2]
    await callback.answer('Отказано без причины')
    db.update_request(request, status='deny')
    await send_request_message(callback, bot, state)


@router.callback_query(F.data.startswith('deny_with_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    i = callback.data.split('_')[2]
    msg = await callback.message.answer('Введите комментарий:', reply_markup=cansel_kb())
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])

    await state.update_data({'msg_id': msg.message_id})
    await state.update_data({'request': i})
    await state.set_state(requests.comment)


@router.callback_query(StateFilter(requests.comment), F.data == 'cansel')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await send_request_message(callback, bot, state)
    await state.set_state(admin.main)


@router.message(StateFilter(requests.comment))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request = data['request']
    await message.delete()
    if not message.text:
        return

    db.update_request(request, status='deny', comment=message.text)
    buttons = [
        [types.InlineKeyboardButton(text='Назад', callback_data='requests_moderation_0')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    msg = await bot.send_message(chat_id=message.chat.id, text='Заявка успешно отклонена!',
                                 reply_markup=keyboard)

    await bot.delete_message(chat_id=message.chat.id, message_id=data['msg_id'])
    await state.set_state(admin.main)
    await state.update_data({'msg_id': msg.message_id})


@router.callback_query(F.data.startswith('allow_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request_id = callback.data.split('_')[1]
    await callback.answer('Одобрено')
    request = db.get_requests(status='active', offset=data['requests_offset'])
    db.update_request(request_id, status='allow')
    db.create_seller(request['name'], request['user_id'], 0, request['phone'], 1,
                     datetime.datetime.now() + datetime.timedelta(days=7), 'active', None, inn=request['inn'])
    await send_request_message(callback, bot, state)
