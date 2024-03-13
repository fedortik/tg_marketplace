from aiogram import F, types, Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto

from admin_panel.main_menu import admin_panel, admin
from utils import models as db

router = Router()


class moderation(StatesGroup):
    main = State()
    goods_rating = State()
    seller_rating = State()


def review_kb(offset, review, count):
    prev_id = (offset - 1) % count
    next_id = (offset + 1) % count
    buttons = []
    one_buttons = [
        types.InlineKeyboardButton(text='⬅️', callback_data='None'),
        types.InlineKeyboardButton(text=f'{offset + 1}/{count}', callback_data="None"),
        types.InlineKeyboardButton(text='➡️', callback_data='None'),
    ]

    navigation_buttons = [
        types.InlineKeyboardButton(text='⬅️', callback_data=f"reviews_moderation_{prev_id}"),
        types.InlineKeyboardButton(text=f'{offset + 1}/{count}', callback_data="None"),
        types.InlineKeyboardButton(text='➡️', callback_data=f"reviews_moderation_{next_id}"),
    ]

    if count == 1:
        buttons.append(one_buttons)
    else:
        buttons.append(navigation_buttons)

    a = [
        types.InlineKeyboardButton(text="Рейтинг товара", callback_data=f"review_goods_rating_{review['goods']}"),
        types.InlineKeyboardButton(text="Рейтинг продавца", callback_data=f"review_seller_rating_{review['goods']}"),
        types.InlineKeyboardButton(text="Удалить", callback_data=f"review_delete_{review['id']}")
    ]
    buttons.append(a)
    buttons.append([types.InlineKeyboardButton(text="Назад", callback_data="admin_panel")])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data.startswith('reviews_moderation_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    offset = int(callback.data.split('_')[2]) if callback.data.split('_')[2] else data['reviews_offset'] if data.get(
        'reviews_offset') else 0
    await state.update_data({'reviews_offset': offset})
    await open_review(callback, state, bot)


async def open_review(callback, state, bot):
    data = await state.get_data()
    reviews_info = db.get_reviews_with_offset(offset=data['reviews_offset'])
    if reviews_info['total_count'] == 0:
        await callback.answer('Нет комментариев', show_alert=True)
        await admin_panel(callback.message, state, bot)
        return
    review = reviews_info['reviews'][0]

    media = [InputMediaPhoto(media=review['photo_doc'], caption=review['comment']),
             InputMediaPhoto(media=review['photo_doc'])]
    msg1 = await bot.send_media_group(chat_id=callback.message.chat.id, media=media)

    goods = db.get_goods_by_id(review['goods'])

    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'
    text += f"Инн поставщика: `" + (str(goods['seller_inn'])) + '`\n'

    text += f"\nОписание: \n\n{goods['description']}\n"

    msg = await bot.send_photo(chat_id=callback.message.chat.id, photo=goods['photo'], caption=text,parse_mode='MARKDOWN',
                               reply_markup=review_kb(data['reviews_offset'], review, reviews_info['total_count']))
    try:
        for i in data['buffer_msg']:
            await bot.delete_message(callback.message.chat.id, i)
    except Exception as e:
        pass
    await bot.delete_message(callback.message.chat.id, data['msg_id'])
    await state.update_data({'msg_id': msg.message_id, 'buffer_msg': [msg1[0].message_id, msg1[1].message_id]})


@router.callback_query(F.data.startswith('review_delete_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    review_id = callback.data.split('_')[2]
    db.delete_review(review_id)
    print(review_id)
    try:
        for i in data['buffer_msg']:
            await bot.delete_message(callback.message.chat.id, i)
    except Exception as e:
        pass
    await bot.delete_message(callback.message.chat.id, data['msg_id'])

    buttons = [
        [types.InlineKeyboardButton(text='Назад', callback_data='reviews_moderation_0')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await bot.send_message(chat_id=callback.message.chat.id, text='Успешно удалено', reply_markup=keyboard)
    await state.update_data({'msg_id': msg.message_id})


@router.callback_query(F.data.startswith('review_goods_rating_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    goods_id = int(callback.data.split('_')[3])
    try:
        for i in data['buffer_msg']:
            await bot.delete_message(callback.message.chat.id, i)
    except Exception as e:
        pass
    await bot.delete_message(callback.message.chat.id, data['msg_id'])

    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='cansel')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await bot.send_message(chat_id=callback.message.chat.id, text='Введите новый рейтинг товара:',
                                 reply_markup=keyboard)
    await state.update_data({'goods_id': goods_id, 'msg_id': msg.message_id})
    await state.set_state(moderation.goods_rating)


@router.message(StateFilter(moderation.goods_rating))
async def update_count(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    try:
        float(message.text)
    except ValueError:
        return
    data = await state.get_data()
    goods_id = data['goods_id']
    db.update_goods(goods_id, rating=message.text)

    buttons = [
        [types.InlineKeyboardButton(text='Назад', callback_data=f"reviews_moderation_{data['reviews_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(admin.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Рейтинг успешно обновлён!',
                                reply_markup=keyboard)


@router.callback_query(F.data.startswith('review_seller_rating_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    goods_id = int(callback.data.split('_')[3])
    try:
        for i in data['buffer_msg']:
            await bot.delete_message(callback.message.chat.id, i)
    except Exception as e:
        pass
    await bot.delete_message(callback.message.chat.id, data['msg_id'])

    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='cansel')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await bot.send_message(chat_id=callback.message.chat.id, text='Введите новый рейтинг поставщика:',
                                 reply_markup=keyboard)
    await state.update_data({'goods_id': goods_id, 'msg_id': msg.message_id})
    await state.set_state(moderation.seller_rating)


@router.message(StateFilter(moderation.seller_rating))
async def update_count(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    try:
        float(message.text)
    except ValueError:
        return
    data = await state.get_data()
    goods_id = data['goods_id']
    db.update_seller_rating_by_goods_id(goods_id, message.text)

    buttons = [
        [types.InlineKeyboardButton(text='Назад', callback_data=f"reviews_moderation_{data['reviews_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(admin.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Рейтинг успешно обновлён!',
                                reply_markup=keyboard)


@router.callback_query(F.data == 'cansel', StateFilter(moderation.goods_rating, moderation.seller_rating))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(moderation.main)
    await open_review(callback, state, bot)
