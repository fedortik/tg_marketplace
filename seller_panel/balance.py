from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from seller_panel.main_menu import seller, seller_main_kb
from utils import models as db

router = Router()


@router.callback_query(F.data == 'balance')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    seller_info = db.get_seller_info(callback.message.chat.id)[0]

    buttons = [
        [
            types.InlineKeyboardButton(text="Пополнить баланс", callback_data="enter_sum"),
        ],
        [
            types.InlineKeyboardButton(text="Назад", callback_data="seller_panel"),
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f"Ваша балланс составляет: {seller_info['balance']}р\nЭтими средставми вы можете оплачивать тарифы.",
                                reply_markup=keyboard)


@router.callback_query(F.data == 'enter_sum')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='seller_panel')],
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите сумму в Российских рублях на которую хотите пополнить балланс(не менее 100р):',
                                reply_markup=keyboard)
    await state.set_state(seller.enter_sum)


@router.message(StateFilter(seller.enter_sum))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text or not message.text.isdigit():
        return
    if int(message.text) < 100:
        return

    PRICE = types.LabeledPrice(label='на сумму', amount=int(message.text) * 100)

    kb = [[InlineKeyboardButton(text='Оплатить', pay=True)],
          [InlineKeyboardButton(text='Отмена', callback_data='cansel')]]

    msg = await bot.send_invoice(
        message.chat.id,
        title='Пополнение балланса',
        description='на сумму',
        provider_token='1744374395:TEST:d4565feccdb610b31f46',
        currency='rub',
        photo_url=None,
        photo_height=512,  # !=0/None, иначе изображение не покажется
        photo_width=512,
        photo_size=512,
        is_flexible=False,  # True если конечная цена зависит от способа доставки
        prices=[PRICE],
        start_parameter='time-machine-example',
        payload='some-invoice-payload-for-our-internal-use',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

    await bot.delete_message(message.chat.id, data['msg_id'])
    await state.update_data({'pay_msg_id': msg.message_id, 'msg_id': 'delete'})

    await state.set_state(seller.pay)


@router.message(StateFilter(seller.pay), F.successful_payment)
async def process_successful_payment(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    pay_data = message.successful_payment
    data = await state.get_data()
    db.add_payment(pay_data.telegram_payment_charge_id, message.chat.id, int(pay_data.total_amount / 100))
    db.add_balance(message.chat.id, int(pay_data.total_amount / 100))
    msg = await bot.send_message(chat_id=message.chat.id,
                                 text='Панель поставщика: ',
                                 reply_markup=seller_main_kb(message.chat.id))
    await state.update_data({'msg_id': msg.message_id})
    await state.set_state(seller.main)
    await bot.delete_message(message.chat.id, data['pay_msg_id'])


@router.pre_checkout_query(StateFilter(seller.pay))
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.callback_query(StateFilter(seller.pay), F.data == 'cansel')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg = await bot.send_message(chat_id=callback.message.chat.id,
                                 text='Панель поставщика: ',
                                 reply_markup=seller_main_kb(callback.message.chat.id))
    await state.update_data({'msg_id': msg.message_id})
    await state.set_state(seller.main)
    await bot.delete_message(callback.message.chat.id, data['pay_msg_id'])
