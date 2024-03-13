from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from utils import models as bd

router = Router()


class seller_registration(StatesGroup):
    li = State()
    name = State()
    fio = State()
    phone = State()
    inn = State()
    inn_doc = State()


def cansel_kb():
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='main_menu_')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data.startswith('start_registration'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    buttons = [
        [
            types.InlineKeyboardButton(text="Физическое лицо", callback_data="li_fiz"),
            types.InlineKeyboardButton(text="Юридическое лицо", callback_data="li_yr"),
        ],
        [types.InlineKeyboardButton(text='Отмена', callback_data='main_menu_')],
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Вы являетесь:',
                                reply_markup=keyboard)
    await state.set_state(seller_registration.li)


@router.callback_query(StateFilter(seller_registration.li), F.data.startswith('li_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    li = 'Физическое лицо' if callback.data.split('_')[1] == 'fiz' else 'Юридическое лицо'
    await state.update_data({'reg_data': {'li': li}})

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Введите название организации:',
                                reply_markup=cansel_kb())
    await state.set_state(seller_registration.name)


@router.message(StateFilter(seller_registration.name))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    reg_data = data['reg_data']
    reg_data['name'] = message.text
    await state.update_data({'reg_data': reg_data})

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Введите ФИО:',
                                reply_markup=cansel_kb())
    await state.set_state(seller_registration.fio)


@router.message(StateFilter(seller_registration.fio))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    reg_data = data['reg_data']
    reg_data['fio'] = message.text
    await state.update_data({'reg_data': reg_data})

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Введите номер телефона:',
                                reply_markup=cansel_kb())
    await state.set_state(seller_registration.phone)


@router.message(StateFilter(seller_registration.phone))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    reg_data = data['reg_data']
    reg_data['phone'] = message.text
    await state.update_data({'reg_data': reg_data})

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Пришлите ИНН:',
                                reply_markup=cansel_kb())
    await state.set_state(seller_registration.inn)


@router.message(StateFilter(seller_registration.inn))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    reg_data = data['reg_data']
    reg_data['inn'] = message.text
    await state.update_data({'reg_data': reg_data})

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Пришлите ИНН в виде документа или фото карточки предприятия::',
                                reply_markup=cansel_kb())
    await state.set_state(seller_registration.inn_doc)


@router.message(StateFilter(seller_registration.inn_doc))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.photo and not message.document:
        return
    data = await state.get_data()
    reg_data = data['reg_data']
    if message.photo:
        reg_data['type'] = 'photo'
        reg_data['file_id'] = message.photo[-1].file_id
    else:
        reg_data['type'] = 'document'
        reg_data['file_id'] = message.document.file_id

    await state.update_data({'reg_data': reg_data})

    buttons = [
        [types.InlineKeyboardButton(text='Вернуться в меню', callback_data='main_menu_')],
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    bd.create_request(reg_data['li'], reg_data['name'], reg_data['fio'], reg_data['type'], reg_data['file_id'],
                      message.chat.id, reg_data['phone'], 'active', '', reg_data['inn'])

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Данные успешно заполненны и отправлены на модерацию',
                                reply_markup=keyboard)
