from aiogram import F, types, Router, Bot
from aiogram.fsm.context import FSMContext

from utils import models as db

router = Router()


@router.callback_query(F.data.startswith('my_orders_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        page = int(callback.data.split('_')[2])
    except (IndexError, ValueError):
        page = 0

    page_size = 10
    orders_info = db.get_orders_by_user(seller_id=callback.message.chat.id, offset=page * page_size, page_size=page_size)

    total_orders = orders_info[0]['orders_count'] if orders_info else 0
    total_pages = (total_orders - 1) // page_size + 1
    if total_orders == 0:
        await callback.answer('У вас пока нет заявок', show_alert=True)
        return
    text = 'Заявки на покупку:\n\n'
    for order in orders_info:
        text += order['buy'] + '\n\n'

    prev_page = (page - 1 + total_pages) % total_pages
    next_page = (page + 1) % total_pages

    one_buttons = [
        [
        types.InlineKeyboardButton(text='⬅️', callback_data='None'),
        types.InlineKeyboardButton(text=f'{page + 1}/{total_pages}', callback_data="None"),
        types.InlineKeyboardButton(text='➡️', callback_data='None'),
        ],
        [types.InlineKeyboardButton(text="Назад", callback_data="seller_panel")]
        ]


    navigation_buttons = [
        [
        types.InlineKeyboardButton(text='⬅️', callback_data=f"my_orders_{prev_page}"),
        types.InlineKeyboardButton(text=f'{page + 1}/{total_pages}', callback_data="None"),
        types.InlineKeyboardButton(text='➡️', callback_data=f"my_orders_{next_page}"),
        ],
        [types.InlineKeyboardButton(text="Назад", callback_data="seller_panel")]
        ]

    if total_orders <= 10:
        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=one_buttons)
    else:
        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=navigation_buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                text=text, reply_markup=reply_markup)
