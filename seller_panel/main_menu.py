from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from utils import models as db

router = Router()


class seller(StatesGroup):
    main = State()
    enter_sum = State()
    pay = State()


def seller_main_kb(chat_id):
    seller_info = db.get_seller_info(chat_id)[0]
    orders_info = db.get_orders_by_user(seller_id=chat_id, offset=0, page_size=1)

    total_orders = orders_info[0]['orders_count'] if orders_info else 0
    buttons = [
        [
            types.InlineKeyboardButton(text="Мои товары", callback_data="seller_my_goods"),
        ],
        [
            types.InlineKeyboardButton(text=f"Заявки на покупку ({total_orders})", callback_data="my_orders_"),
        ],
        [
            types.InlineKeyboardButton(text=f"Балланс: {seller_info['balance']}р", callback_data="balance"),
            types.InlineKeyboardButton(text=f"Тариф: {seller_info['tarif_name']}", callback_data="tarif"),
        ],
        [
            types.InlineKeyboardButton(text="Выйти", callback_data="main_menu_"),
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data.startswith('seller_panel'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request = db.get_request(callback.message.chat.id)

    if not request:
        buttons = [
            [
                types.InlineKeyboardButton(text="Начать регистрацию", callback_data="start_registration"),
            ],
            [
                types.InlineKeyboardButton(text="Назад", callback_data="main_menu_"),
            ]
        ]

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                    text='Вы ещё не зарегистрированны как поставщик!',
                                    reply_markup=keyboard)
        return

    if request['status'] == 'active':
        await callback.answer('Ваша заявка на регистрацию ещё на рассмотрении!\nМы сообщим, когда её одобрят!',
                              show_alert=True)
        return
    elif request['status'] == 'deny':
        text = 'Ваша заявка была отклонена!'
        if request['comment']:
            text += '\nПо причине: ' + request['comment']
        await callback.answer(text, show_alert=True)
        return
    elif request['status'] == 'ban':
        text = 'Вы были забанены!'
        if request['comment'] :
            text += '\nПо причине: ' + request['comment']
        await callback.answer(text, show_alert=True)
        return
    try:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                    text='Панель поставщика: ',
                                    reply_markup=seller_main_kb(callback.message.chat.id))
    except:
        msg = await bot.send_message(chat_id=callback.message.chat.id, text='Панель поставщика: ',
                               reply_markup=seller_main_kb(callback.message.chat.id))
        await bot.delete_message(callback.message.chat.id, data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})
    await state.set_state(seller.main)


@router.message(StateFilter(seller.main))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
