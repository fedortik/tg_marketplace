from aiogram import Router, types, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()
from utils import models as db

class admin(StatesGroup):
    main = State()


def admin_kb():
    request = db.get_requests(status='active', offset=0)
    if request:
        count = request.get('total_count', 0)
    else:
        count = 0
    reviews_info = db.get_reviews_with_offset(offset=0)
    buttons = [
        [
            types.InlineKeyboardButton(text="Редактировать", callback_data="start_edit"),
        ],
        [
            types.InlineKeyboardButton(text="Редактировать тарифы", callback_data="edittarifs"),
        ],
        [
            types.InlineKeyboardButton(text=f"Поставщики на модерацию({count})",
                                       callback_data="requests_moderation_0"),
        ],
        [
            types.InlineKeyboardButton(text=f"Забанить поставщика",
                                       callback_data="ban_seller_0"),
        ],
        [
            types.InlineKeyboardButton(text=f"Заявки на покупку",
                                       callback_data="all_orders_0_"),
        ],
        [
            types.InlineKeyboardButton(text=f"Модерация отзывов({reviews_info['total_count']})",
                                       callback_data="reviews_moderation_0"),
        ],
        [
            types.InlineKeyboardButton(text=f"Добавить в бан лист",
                                       callback_data="add_ban_list"),
        ],
        [
            types.InlineKeyboardButton(text="Выйти", callback_data="main_menu_"),
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data == 'admin_panel')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await admin_panel(callback.message, state, bot)



@router.message(StateFilter(admin.main))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()


async def admin_panel(message, state, bot):
    data = await state.get_data()
    await state.set_state(admin.main)
    msg = await bot.send_message(chat_id=message.chat.id,
                                 text='Админ панель: ',
                                 reply_markup=admin_kb())

    try:

        await bot.delete_message(chat_id=message.chat.id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})
    except Exception as e:
        print(e)

    try:
        for i in data['buffer_msg']:
            await bot.delete_message(message.chat.id, i)
    except Exception as e:
        pass

