from aiogram import F, types, Router, Bot
from aiogram.fsm.context import FSMContext

from utils import models as db

router = Router()


@router.callback_query(F.data.startswith('all_orders_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    page = int(callback.data.split('_')[2]) if callback.data.split('_')[2] else 0
    date_filter = callback.data.split('_')[3] if callback.data.split('_')[3] else data['date_filter'] if data.get(
        'date_filter') else None
    await state.update_data({'date_filter': date_filter})

    page_size = 10
    orders_info = db.get_orders_by_user(offset=page * page_size, page_size=page_size, date_filter=date_filter)
    buttons = []
    total_orders = orders_info[0]['orders_count'] if orders_info else 0
    total_pages = (total_orders - 1) // page_size + 1
    if total_orders > 0:
        text = f'Заявки на покупку ({date_filter}):\n\n'
        for order in orders_info:
            text += f"У {order['seller_name']} {order['buy']}\n\n"

            prev_page = (page - 1 + total_pages) % total_pages
            next_page = (page + 1) % total_pages

        one_buttons = [
            types.InlineKeyboardButton(text='⬅️', callback_data='None'),
            types.InlineKeyboardButton(text=f'{page + 1}/{total_pages}', callback_data="None"),
            types.InlineKeyboardButton(text='➡️', callback_data='None'),
        ]

        navigation_buttons = [
            types.InlineKeyboardButton(text='⬅️', callback_data=f"my_orders_{prev_page}"),
            types.InlineKeyboardButton(text=f'{page + 1}/{total_pages}', callback_data="None"),
            types.InlineKeyboardButton(text='➡️', callback_data=f"my_orders_{next_page}"),
        ]

        if total_orders <= 10:
            buttons.append(one_buttons)
        else:
            buttons.append(navigation_buttons)
    else:
        text = f'С текущим фильтром заявок нет! ({date_filter})'

    a = [
        types.InlineKeyboardButton(text="За сегодня", callback_data="filter_today"),
        types.InlineKeyboardButton(text="За месяц", callback_data="filter_month"),
        types.InlineKeyboardButton(text="За всё время", callback_data="filter_none")
    ]
    buttons.append(a)
    buttons.append([types.InlineKeyboardButton(text="Назад", callback_data="admin_panel")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                text=text, reply_markup=keyboard)


@router.callback_query(F.data.startswith('filter_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    date_filter = callback.data.split('_')[1]
    await state.update_data({'date_filter': date_filter})
    buttons = [
        [types.InlineKeyboardButton(text='Назад', callback_data='all_orders_0_')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                text='Фильтер изменён', reply_markup=keyboard)
