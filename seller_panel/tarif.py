import datetime

from aiogram import F, types, Router, Bot
from aiogram.fsm.context import FSMContext

from utils import models as db

router = Router()


@router.callback_query(F.data == 'tarif')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    seller_info = db.get_seller_info(callback.message.chat.id)[0]

    buttons = [
        [
            types.InlineKeyboardButton(text="Узнать о тарифах", callback_data="tarif_info"),
        ],
        [
            types.InlineKeyboardButton(text="Активировать PREMIUM", callback_data="activate_PREMIUM"),
            types.InlineKeyboardButton(text="Активировать VIP", callback_data="activate_VIP"),
        ],
        [
            types.InlineKeyboardButton(text="Активировать GOLD", callback_data="activate_GOLD"),
            types.InlineKeyboardButton(text="Активировать GOLD+", callback_data="activate_GOLD+"),
        ],
        [
            types.InlineKeyboardButton(text="Деактивировать текущий тариф", callback_data="deactivate")
        ],
        [
            types.InlineKeyboardButton(text="Назад", callback_data="seller_panel"),
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f"Ваш текущий тариф: {seller_info['tarif_name']}\nДействует {'до: '+seller_info['tarif_end'][0:11] if seller_info['tarif_name'] != 'FREE' else 'бессрочно'}",
                                reply_markup=keyboard)


@router.callback_query(F.data == 'tarif_info')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tarifs = db.get_tarifs()
    text = ''
    for name, value in tarifs.items():
        text += f"{name} - стоит {str(value['amount']) + 'р' if value['amount'] != 0.0 else 'бесплатно'} даётся на {str(value['days']) + 'дней' if value['days'] != 999 else 'всегда'}  и позволяет публиковать {value['publications']} товаров\n"

    buttons = [
        [
            types.InlineKeyboardButton(text="Назад", callback_data="tarif"),
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=text,
                                reply_markup=keyboard)


@router.callback_query(F.data.startswith('activate_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    seller_info = db.get_seller_info(callback.message.chat.id)[0]
    tarif_name = callback.data.split('_')[1]
    tarifs = db.get_tarifs()

    if seller_info['tarif_name'] != 'FREE':
        await callback.answer(
            f"У вас уже активирован тариф {seller_info['tarif_name']}!\nДля начала деактивируйте ткущий тариф!",
            show_alert=True)
    if seller_info['balance'] < tarifs.get(tarif_name)['amount']:
        await callback.answer('Недостаточно средств на балансе!', show_alert=True)
        return

    db.rem_balance(callback.message.chat.id, tarifs.get(tarif_name)['amount'])

    db.update_seller(callback.message.chat.id,
                     {'tarif': tarifs.get(tarif_name)['id'],
                      'tarif_end': datetime.datetime.today() + datetime.timedelta(days=30)})

    buttons = [
        [
            types.InlineKeyboardButton(text="Назад", callback_data="tarif"),
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Тариф {tarif_name} успешно активирован!',
                                reply_markup=keyboard)


@router.callback_query(F.data == 'deactivate')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    seller_info = db.get_seller_info(callback.message.chat.id)[0]
    tarifs = db.get_tarifs()
    tarif_name = seller_info['tarif_name']

    if tarif_name == 'FREE':
        await callback.answer(
            'Нельзя деактивировать товари FREE !',
            show_alert=True)
        return

    ost_days = (datetime.datetime.strptime(seller_info['tarif_end'], '%Y-%m-%d %H:%M:%S.%f') - datetime.datetime.now()).days

    ost_money = int(int(tarifs[tarif_name]['amount']) / int(tarifs[tarif_name]['days']) * int(ost_days))

    db.add_balance(callback.message.chat.id, ost_money)

    db.update_seller(callback.message.chat.id,
                     {'tarif': tarifs.get("FREE")['id'],
                      'tarif_end': datetime.datetime.today() + datetime.timedelta(days=30)})

    buttons = [
        [
            types.InlineKeyboardButton(text="Назад", callback_data="tarif"),
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Тариф {tarif_name} успешно деактивирован!\n Средства за непотраченые дни вернулись на балланс!',
                                reply_markup=keyboard)



