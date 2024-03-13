from aiogram import Router, types, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from admin_panel.main_menu import admin
from utils import models as db

router = Router()


class tarifs(StatesGroup):
    edit_amount = State()
    edit_publications = State()

def cansel_kb():
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='cansel')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def open_tarif_kb(tarif_name):
    tarifs = db.get_tarifs()
    buttons = [[
        types.InlineKeyboardButton(text=f"Стоимость: {tarifs[tarif_name]['amount']}",
                                   callback_data=f"editamount_{tarif_name}"),
        types.InlineKeyboardButton(text=f"Количество публикаций: {tarifs[tarif_name]['publications']}",
                                   callback_data=f'editpublications_{tarif_name}'),
    ], [types.InlineKeyboardButton(text='Назад', callback_data=f'edittarifs')]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data == 'edittarifs')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tarifs = db.get_tarifs()
    buttons = []
    for name, value in tarifs.items():
        buttons.append([types.InlineKeyboardButton(text=name, callback_data=f"opentarif_{name}")])

    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data=f'admin_panel')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Тарифы: ',
                                reply_markup=keyboard)


@router.callback_query(F.data.startswith('opentarif_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tarif_name = callback.data.split('_')[1]

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Тариф {tarif_name}: ',
                                reply_markup=open_tarif_kb(tarif_name))


@router.callback_query(F.data.startswith('editamount_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tarif_name = callback.data.split('_')[1]

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите новую цену тарифа: ',
                                reply_markup=cansel_kb())
    await state.update_data({'tarif_name': tarif_name})
    await state.set_state(tarifs.edit_amount)


@router.message(StateFilter(tarifs.edit_amount))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tarif_name = data['tarif_name']
    await message.delete()
    if not message.text or not message.text.isdigit():
        return
    db.update_tarif(tarif_name, amount=message.text)
    await state.set_state(admin.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text=f'Тариф {tarif_name}: ',
                                reply_markup=open_tarif_kb(tarif_name))


@router.callback_query(F.data.startswith('editpublications_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tarif_name = callback.data.split('_')[1]

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите новую количество публикаций: ',
                                reply_markup=cansel_kb())
    await state.update_data({'tarif_name': tarif_name})
    await state.set_state(tarifs.edit_publications)


@router.message(StateFilter(tarifs.edit_publications))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tarif_name = data['tarif_name']
    await message.delete()
    if not message.text or not message.text.isdigit():
        return

    db.update_tarif(tarif_name, publications=message.text)
    await state.set_state(admin.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text=f'Тариф {tarif_name}: ',
                                reply_markup=open_tarif_kb(tarif_name))


@router.callback_query(StateFilter(tarifs.edit_amount, tarifs.edit_publications), F.data == 'cansel')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tarifs = db.get_tarifs()
    buttons = []
    for name, value in tarifs.items():
        buttons.append([types.InlineKeyboardButton(text=name, callback_data=f"opentarif_{name}")])

    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data=f'admin_panel')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Тарифы: ',
                                reply_markup=keyboard)
    await state.set_state(admin.main)