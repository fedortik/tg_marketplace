from aiogram import Router, types, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from admin_panel.main_menu import admin, admin_panel
from utils import models as db

router = Router()


class ban_list(StatesGroup):
    enter = State()


@router.callback_query(F.data == 'add_ban_list')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='cansel')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите текст:',
                                reply_markup=keyboard)
    await state.set_state(ban_list.enter)


@router.message(StateFilter(ban_list.enter))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return

    db.add_ban_record(message.text)
    await state.set_state(admin.main)
    buttons = [
        [types.InlineKeyboardButton(text='Назад', callback_data='admin_panel')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Запись добавлена!',
                                reply_markup=keyboard)


@router.callback_query(StateFilter(ban_list.enter), F.data == 'cansel')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await admin_panel(callback.message, state, bot)
    await state.set_state(admin.main)
