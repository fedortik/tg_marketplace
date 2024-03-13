import datetime

from aiogram import Router, types, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from admin_panel.main_menu import admin, admin_panel
from utils import models as db

router = Router()


class ban(StatesGroup):
    comment = State()
    f = State()


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
    buttons.append([types.InlineKeyboardButton(text="Забанить c причиной", callback_data=f"ban_with_{request_id}")])
    buttons.append([types.InlineKeyboardButton(text="Забанить без причины", callback_data=f"ban_without_{request_id}")])
    buttons.append([types.InlineKeyboardButton(text="Назад", callback_data="admin_panel")])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def cansel_kb():
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='cansel')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data.startswith('ban_seller_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    offset = int(callback.data.split('_')[2])
    await state.update_data({'requests_offset': offset})
    await send_request_message(callback, bot, state)


async def send_request_message(callback, bot, state):
    data = await state.get_data()
    requests = db.get_requests(status='allow', offset=data['requests_offset'])

    if not requests or not requests.get('total_count'):
        await callback.answer('Не активных поставщиков', show_alert=True)
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


@router.callback_query(F.data.startswith('ban_without_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request_id = callback.data.split('_')[2]
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='cansel')],
        [types.InlineKeyboardButton(text='Подтвердлить бан', callback_data=f'ban_without1_{request_id}')],
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await callback.message.answer('Уверены?', reply_markup=keyboard)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])

    await state.update_data({'msg_id': msg.message_id})

    await state.set_state(ban.f)


@router.callback_query(F.data.startswith('ban_without1_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request_id = callback.data.split('_')[2]
    await callback.answer('Забанили без причины')
    requests = db.get_requests(status='allow', offset=data['requests_offset'])
    db.update_request(request_id, status='ban')
    db.update_goods_status_by_seller(requests['user_id'], 'disabel')
    await send_request_message(callback, bot, state)


@router.callback_query(F.data.startswith('ban_with_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    i = callback.data.split('_')[2]
    msg = await callback.message.answer('Введите комментарий:', reply_markup=cansel_kb())
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])

    await state.update_data({'msg_id': msg.message_id})
    await state.update_data({'request': i})
    await state.set_state(ban.comment)


@router.callback_query(StateFilter(ban.comment, ban.f), F.data == 'cansel')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await send_request_message(callback, bot, state)
    await state.set_state(admin.main)


@router.message(StateFilter(ban.comment))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request_id = data['request']
    await message.delete()
    if not message.text:
        return
    request = db.get_requests(status='allow', offset=data['requests_offset'])
    db.update_request(request_id, status='ban', comment=message.text)
    db.update_goods_status_by_seller(request['user_id'], 'disabel')
    buttons = [
        [types.InlineKeyboardButton(text='Назад', callback_data='ban_seller_0')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    msg = await bot.send_message(chat_id=message.chat.id, text='Поставщик забанен!',
                                 reply_markup=keyboard)

    await bot.delete_message(chat_id=message.chat.id, message_id=data['msg_id'])
    await state.set_state(admin.main)
    await state.update_data({'msg_id': msg.message_id})

