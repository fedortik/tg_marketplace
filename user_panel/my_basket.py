from aiogram import F, types, Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto

from utils import models as db

router = Router()


class basket(StatesGroup):
    main = State()
    edit_count = State()
    enter_phone = State()


def goods_kb(offset, goods):
    buttons = []
    basket_count = goods['basket_count']
    prev_id = (offset - 1) % basket_count
    next_id = (offset + 1) % basket_count

    if basket_count == 1:
        buttons.append([
            types.InlineKeyboardButton(text='⬅️⬅️⬅️', callback_data="None"),
            types.InlineKeyboardButton(text='1/1', callback_data="None"),
            types.InlineKeyboardButton(text='➡️➡️➡️', callback_data="None")
        ])
    else:
        buttons.append([
            types.InlineKeyboardButton(text='⬅️⬅️⬅️',
                                       callback_data=f"my_basket_{prev_id}"),
            types.InlineKeyboardButton(text=f'{offset + 1}/{basket_count}', callback_data="None"),
            types.InlineKeyboardButton(text='➡️➡️➡️',
                                       callback_data=f"my_basket_{next_id}")
        ])

    buttons.append(
        [
            types.InlineKeyboardButton(text='Изменить заявку',
                                       callback_data=f"basket_change_{goods['id']}"),
            types.InlineKeyboardButton(text='Удалить из корзины', callback_data=f"basket_delete_{goods['id']}")
        ]
    )

    buttons.append([types.InlineKeyboardButton(text='Купить всё', callback_data=f'basket_buy_all')])
    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data=f'main_menu_')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data.startswith('my_basket_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    offset = int(callback.data.split('_')[2]) if callback.data.split('_')[2] else 0
    await state.update_data({'basket_offset': offset})
    data = await state.get_data()
    goods_data = db.get_basket(callback.message.chat.id, data['basket_offset'])[0]
    if not goods_data.get('goods'):
        await callback.answer('Ваша корзина пуста', show_alert=True)
        return
    await open_goods(callback.message.chat.id, state, bot)


async def open_goods(chat_id, state, bot):
    data = await state.get_data()
    goods_data = db.get_basket(chat_id, data['basket_offset'])[0]
    if not goods_data.get('goods') and goods_data.get('basket_count') == 0:
        buttons = [[types.InlineKeyboardButton(text='Назад', callback_data=f'main_menu_')]]

        msg = await bot.send_message(chat_id=chat_id,
                                     text='Ваша корзина пуста',
                                     reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
        await bot.delete_message(chat_id=chat_id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})
        return
    if not goods_data.get('goods'):
        data['basket_offset'] -= 1
        await state.update_data({'basket_offset': data['basket_offset']})
        goods_data = db.get_basket(chat_id, data['basket_offset'])[0]
    goods = goods_data['goods']
    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'
    text += f"Инн поставщика: `" + (str(goods['seller_inn'])) + '`\n'

    text += f"\nОписание: \n\n{goods['description']}\n"

    text += f"\nВы хотите приобрести:\n{goods_data['count']}"

    try:
        await bot.edit_message_media(chat_id=chat_id, message_id=data['msg_id'],
                                     media=InputMediaPhoto(media=goods['photo'], caption=text, parse_mode='MARKDOWN'),
                                     reply_markup=goods_kb(data['basket_offset'], goods_data))
    except:
        msg = await bot.send_photo(chat_id=chat_id, photo=goods['photo'], caption=text, parse_mode='MARKDOWN',
                                   reply_markup=goods_kb(data['basket_offset'], goods_data))
        await bot.delete_message(chat_id=chat_id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})


@router.callback_query(F.data.startswith('basket_delete_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    basket_id = int(callback.data.split('_')[2])
    db.delete_basket_by_id(basket_id)
    await open_goods(callback.message.chat.id, state, bot)


@router.callback_query(F.data.startswith('basket_change_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    basket_id = int(callback.data.split('_')[2])
    await state.update_data({'basket_change': basket_id})

    goods = db.get_basket(callback.message.chat.id, data['basket_offset'])[0]['goods']

    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data=f"my_basket_{data['basket_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'
    text += f"Инн поставщика: `" + (str(goods['seller_inn'])) + '`\n'

    text += f"\nОписание: \n\n{goods['description']}\n"

    text += f"\nВведите что и в каком количестве вы хотите приобрести:"

    await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                 media=InputMediaPhoto(media=goods['photo'], caption=text, parse_mode='MARKDOWN'),
                                 reply_markup=keyboard)

    await state.set_state(basket.edit_count)


@router.message(StateFilter(basket.edit_count))
async def update_description(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    basket_change = data['basket_change']
    goods = db.get_basket(message.chat.id, data['basket_offset'])[0]['goods']
    db.update_basket_record(basket_change, message.text)
    await state.set_state(basket.main)
    await open_goods(message.chat.id, state, bot)


@router.callback_query(F.data == 'basket_buy_all')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data=f"my_basket_{data['basket_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await bot.send_message(chat_id=callback.message.chat.id,
                                 text='Предоставьте ваш номер телефона для того что бы менеджер поставщика связался с вами:',
                                 reply_markup=keyboard)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])
    await state.update_data({'msg_id': msg.message_id})
    await state.set_state(basket.enter_phone)


@router.message(StateFilter(basket.enter_phone))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return

    basket_list = db.get_basket(message.chat.id, data['basket_offset'], limit=100000)
    print(len(basket_list))
    for bask in basket_list:
        order_text = f"{message.text} хочет приобрести {bask['goods']['goods_category']} в количестве {data['goods_count']}шт по цене {bask['goods']['price']}р"
        db.create_order(order_text, bask['goods']['seller_id'], message.chat.id, bask['goods']['id'])
        db.delete_basket_by_id(bask['id'])
        await bot.send_message(bask['goods']['seller_id'], order_text)

    buttons = [
        [types.InlineKeyboardButton(text='Назад', callback_data=f'main_menu_')],
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Заявка успешно оформлена, с вам свяжутся в ближайшее время!',
                                reply_markup=keyboard)
    await state.set_state(basket.main)
