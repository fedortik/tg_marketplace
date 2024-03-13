from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from utils import models as bd

router = Router()


def support_kb():
    buttons = []
    support = bd.get_support()
    for name, username in support.items():
        buttons.append([types.InlineKeyboardButton(text=name, url=f"http://t.me/{username}")])
    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data="main_menu_")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


class menu(StatesGroup):
    support = State()


@router.callback_query(F.data == "support")
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if await state.get_state() == menu.support:
        return
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'], text='Поддержка:',
                                reply_markup=support_kb())
    await state.set_state(menu.support)
