from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto

from user_panel.main_catalog import menu
from utils import models as db

router = Router()


class reviews(StatesGroup):
    enter_photo_doc = State()
    enter_photo_goods = State()
    enter_comment = State()


@router.callback_query(F.data == 'create_reviews')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data=f"my_buy_{data['my_buy_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await bot.send_message(chat_id=callback.message.chat.id,
                                 text=f'Пришлите фото документа подтверждающего покупку:',
                                 reply_markup=keyboard)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])
    await state.update_data({'msg_id': msg.message_id})
    await state.set_state(reviews.enter_photo_doc)


@router.message(StateFilter(reviews.enter_photo_doc))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.photo:
        return

    await state.update_data({'review_photo_doc': message.photo[-1].file_id})
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data=f"my_buy_{data['my_buy_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Пришлите фото товара:',
                                reply_markup=keyboard)
    await state.set_state(reviews.enter_photo_goods)


@router.message(StateFilter(reviews.enter_photo_goods))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.photo:
        return

    await state.update_data({'review_photo_goods': message.photo[-1].file_id})
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data=f"my_buy_{data['my_buy_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Введите ваш отзыв о поставщике и товаре:',
                                reply_markup=keyboard)
    await state.set_state(reviews.enter_comment)


@router.message(StateFilter(reviews.enter_comment))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return

    db.create_review(data['my_buy_goods_id'], message.text, data['review_photo_doc'], data['review_photo_goods'])

    buttons = [
        [types.InlineKeyboardButton(text='Назад',
                                    callback_data=f"my_buy_{data['my_buy_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Отзыв отправлен на модерацию!',
                                reply_markup=keyboard)
    await state.set_state(menu.main_catalog)
