from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

from seller_panel.main_menu import seller, seller_main_kb
from utils import models as db

router = Router()


class seller_create_goods(StatesGroup):
    photo = State()
    description = State()
    height = State()
    price = State()
    count = State()


def cansel_kb(name):
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data=f'seller_open_goods_{name}_0')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data == 'seller_create_goods')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if callback.message.photo:
        msg = await bot.send_message(chat_id=callback.message.chat.id,
                                     text='Пришлите фото товара:', reply_markup=cansel_kb(data['goods_category']))
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})
    else:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                    text='Пришлите фото товара:', reply_markup=cansel_kb(data['goods_category']))
    await state.set_state(seller_create_goods.photo)


@router.message(StateFilter(seller_create_goods.photo))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.photo:
        return
    data = await state.get_data()
    await state.update_data({'create_data': {'photo': message.photo[-1].file_id}})

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Пример:\n1.5м - 1500р - 23штn\n2м - 2000р - 110шт\nВведите описание товара как показано в примере:',

                                reply_markup=cansel_kb(data['goods_category']))
    await state.set_state(seller_create_goods.description)


@router.message(StateFilter(seller_create_goods.description))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    create_data = data['create_data']
    create_data['description'] = message.text
    await state.update_data({'create_data': create_data})

    db.create_goods(create_data['description'], create_data['photo'], None, None,
                    None, data['goods_category'], message.chat.id, 'disabel')

    buttons = [
        [types.InlineKeyboardButton(text='К товарам',
                                    callback_data=f"seller_open_goods_{data['goods_category']}_0")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Товар успешно создан, осталось лишь активировать его, что бы его увидели все покупатели!',
                                reply_markup=keyboard)
    await state.set_state(seller.main)



@router.message(StateFilter(seller_create_goods.count))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text or not message.text.isdigit():
        return
    data = await state.get_data()
    create_data = data['create_data']
    create_data['count'] = message.text
    await state.update_data({'create_data': create_data})

    db.create_goods(create_data['description'], create_data['photo'], create_data['height'], create_data['price'],
                          create_data['count'], data['goods_category'], message.chat.id, 'disabel')

    buttons = [
        [types.InlineKeyboardButton(text='К товарам',
                                    callback_data=f"seller_open_goods_{data['goods_category']}_0")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Товар успешно создан, осталось лишь активировать его, что бы его увидели все покупатели!',
                                reply_markup=keyboard)
    await state.set_state(seller.main)
