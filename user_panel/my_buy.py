from aiogram import F, types, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto

from utils import models as db

router = Router()


def goods_kb(offset, count):
    buttons = []
    prev_id = (offset - 1) % count
    next_id = (offset + 1) % count

    if count == 1:
        buttons.append([
            types.InlineKeyboardButton(text='⬅️⬅️⬅️', callback_data="None"),
            types.InlineKeyboardButton(text='1/1', callback_data="None"),
            types.InlineKeyboardButton(text='➡️➡️➡️', callback_data="None")
        ])
    else:
        buttons.append([
            types.InlineKeyboardButton(text='⬅️⬅️⬅️',
                                       callback_data=f"my_buy_{prev_id}"),
            types.InlineKeyboardButton(text=f'{offset + 1}/{count}', callback_data="None"),
            types.InlineKeyboardButton(text='➡️➡️➡️',
                                       callback_data=f"my_buy_{next_id}")
        ])

    buttons.append([types.InlineKeyboardButton(text='Оставить отзыв', callback_data=f'create_reviews')])
    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data=f'main_menu_')])

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith('my_buy_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    offset = int(callback.data.split('_')[2]) if callback.data.split('_')[2] else 0

    orders_info = db.get_orders_by_user(user_id=callback.message.chat.id, offset=offset, page_size=1)[0]
    total_orders = orders_info['orders_count'] if orders_info else 0
    if total_orders == 0:
        await callback.answer('Вы пока ничего не купили', show_alert=True)
        return
    goods = db.get_goods_by_id(orders_info['goods_id'])
    await state.update_data({'my_buy_offset': offset, 'my_buy_goods_id': orders_info['goods_id']})
    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'
    text += f"Инн поставщика: `" + (str(goods['seller_inn'])) + '`\n'

    text += f"\nОписание: \n\n{goods['description']}\n"

    try:
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                     media=InputMediaPhoto(media=goods['photo'], caption=text, parse_mode='MARKDOWN'),
                                     reply_markup=goods_kb(offset, total_orders))
    except:
        msg = await bot.send_photo(chat_id=callback.message.chat.id, photo=goods['photo'], caption=text,parse_mode='MARKDOWN',
                                   reply_markup=goods_kb(offset, total_orders))
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})
