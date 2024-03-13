from aiogram import F, types, Router, Bot
from aiogram.fsm.context import FSMContext

from utils import models as db

router = Router()


@router.callback_query(F.data.startswith('ban_list_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    offset = int(callback.data.split('_')[2]) if callback.data.split('_')[2] else 0

    count, ban_list = db.get_ban_records_with_offset(limit=10, offset=offset)
    print(count, ban_list)
    buttons = []
    total_pages = (count - 1) // 10 + 1
    if count == 0:
        await callback.answer('Чёрный список пока пуст!', show_alert=True)
        return

    text = f'Чёрный список поставщиков:\n\n'
    for ban in ban_list:
        text += f'{ban}\n\n'

    # Исправленные расчеты для перелистывания страниц
    prev_page = ((offset - 1) + total_pages) % total_pages
    next_page = ((offset + 1) % total_pages)
    current_page = (offset // 10) + 1  # Предполагаем, что limit = 10

    # Условия и кнопки обновлены с учетом исправлений
    if total_pages > 1:
        navigation_buttons = [
            types.InlineKeyboardButton(text='⬅️', callback_data=f"ban_list_{prev_page*10}"),  # Умножаем, чтобы получить смещение
            types.InlineKeyboardButton(text=f'{current_page}/{total_pages}', callback_data="None"),
            types.InlineKeyboardButton(text='➡️', callback_data=f"ban_list_{next_page*10}"),
        ]
        buttons.append(navigation_buttons)
    else:
        # Можете решить, нужны ли кнопки для одной страницы или нет
        pass

    buttons.append([types.InlineKeyboardButton(text="Назад", callback_data="main_menu_")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                text=text, reply_markup=keyboard)


