from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto

from user_panel.main_catalog import menu
from utils import models as db

router = Router()


class order(StatesGroup):
    enter_count = State()
    enter_phone = State()


@router.callback_query(F.data.startswith('main_buy_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    goods_id = int(callback.data.split('_')[2])
    await state.update_data({'goods_id': goods_id})
    goods = db.get_goods_by_id(goods_id)

    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data=f"main_goods_{data['goods_category']}_{goods_id}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'
    text += f"Инн поставщика: `" + (str(goods['seller_inn'])) + '`\n'

    text += f"\nОписание: \n\n{goods['description']}\n"

    text += "\nВведите что и в каком количестве вы хотите приобрести:"

    await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                 media=InputMediaPhoto(media=goods['photo'], caption=text, parse_mode='MARKDOWN'),
                                 reply_markup=keyboard)

    await state.set_state(order.enter_count)


@router.message(StateFilter(order.enter_count))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return
    goods = db.get_goods_by_id(data['goods_id'])

    await state.update_data({'goods_count': message.text})
    buttons = [
        [types.InlineKeyboardButton(text='Отмена',
                                    callback_data=f"main_goods_{data['goods_category']}_{data['goods_id']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'
    text += f"Инн поставщика: `" + (str(goods['seller_inn'])) + '`\n'

    text += f"\nОписание: \n\n{goods['description']}\n"

    text += "\nВведите ваш номер телефона для связи:"

    await bot.edit_message_media(chat_id=message.chat.id, message_id=data['msg_id'],
                                 media=InputMediaPhoto(media=goods['photo'], caption=text, parse_mode='MARKDOWN'),
                                 reply_markup=keyboard)
    await state.set_state(order.enter_phone)


@router.message(StateFilter(order.enter_phone))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return
    goods = db.get_goods_by_id(data['goods_id'])
    order_text = f"{message.text} хочет приобрести {goods['goods_category']}\n {data['goods_count']}"
    db.create_order(order_text, goods['seller_id'], message.chat.id, data['goods_id'])
    await bot.send_message(goods['seller_id'], order_text)

    buttons = [
        [types.InlineKeyboardButton(text='Назад к товарам',
                                    callback_data=f"main_goods_{data['goods_category']}_{data['goods_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'
    text += f"Инн поставщика: `" + (str(goods['seller_inn'])) + '`\n'

    text += f"\nОписание: \n\n{goods['description']}\n"

    text += "\nЗаявка на покупку успешно оформлена!\n Поставщик свяжется в вами в билжайшее время!"

    await bot.edit_message_media(chat_id=message.chat.id, message_id=data['msg_id'],
                                 media=InputMediaPhoto(media=goods['photo'], caption=text, parse_mode='MARKDOWN'),
                                 reply_markup=keyboard)
    await state.set_state(menu.main_catalog)
