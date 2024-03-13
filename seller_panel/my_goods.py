from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

from seller_panel.main_menu import seller, seller_main_kb
from utils import models as db

router = Router()


class change(StatesGroup):
    photo = State()
    description = State()
    height = State()
    count = State()
    price = State()


def categories_kb(chat_id):
    categories = db.get_all_categories_seller(chat_id)

    buttons = []
    for i in range(0, len(categories), 2):
        row_buttons = categories[i:i + 2]
        buttons.append([
            types.InlineKeyboardButton(text=pod_cat['name'] + f" ({pod_cat['count']})",
                                       callback_data=f"seller_open_cat_{pod_cat['id']}")
            for pod_cat in row_buttons
        ])

    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data='seller_panel')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def pod_categories_kb(categories_name, chat_id):
    pod_categories = db.get_all_pod_categories(categories_name, chat_id)
    buttons = []

    for i in range(0, len(pod_categories), 2):
        row_buttons = pod_categories[i:i + 2]
        buttons.append([
            types.InlineKeyboardButton(text=pod_cat['name'] + f" ({pod_cat['count']})",
                                       callback_data=f"seller_open_pod_cat_{pod_cat['id']}")
            for pod_cat in row_buttons
        ])

    buttons.extend([
        [types.InlineKeyboardButton(text='Назад', callback_data='seller_my_goods')],
        [types.InlineKeyboardButton(text='На главную', callback_data='seller_panel')]
    ])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def pod_pod_categories_kb(pod_categories_id, categories_id, chat_id):
    pod_pod_categories = db.get_all_goods_categories(pod_categories_id, user_id=chat_id)
    buttons = []

    for i in range(0, len(pod_pod_categories), 2):
        row_buttons = pod_pod_categories[i:i+2]
        buttons.append([
            types.InlineKeyboardButton(text=name['name'] + f" ({name['count']})",
                                       callback_data=f"seller_open_goods_{name['id']}_")
            for name in row_buttons
        ])

    buttons.extend([
        [types.InlineKeyboardButton(text='Назад', callback_data=f'seller_open_cat_{categories_id}')],
        [types.InlineKeyboardButton(text='На главную', callback_data=f'seller_panel')]
    ])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def zero_goods_kb(name):
    buttons = [[types.InlineKeyboardButton(text='Создать новый товар', callback_data=f'seller_create_goods')],
               [types.InlineKeyboardButton(text='Назад', callback_data=f'seller_open_pod_cat_{name}')],
               [types.InlineKeyboardButton(text='На главную', callback_data=f'seller_panel')]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def goods_kb(offset, goods, goods_categories_id, pod_categories_id, activ_goods, allow_publications):
    buttons = []
    goods_count = goods['goods_count']
    prev_id = (offset - 1) % goods_count
    next_id = (offset + 1) % goods_count
    if goods['goods_count'] == 1:
        buttons.append([
            types.InlineKeyboardButton(text='⬅️⬅️⬅️', callback_data="None"),
            types.InlineKeyboardButton(text='1/1', callback_data="None"),
            types.InlineKeyboardButton(text='➡️➡️➡️', callback_data="None")
        ])
    else:
        buttons.append([
            types.InlineKeyboardButton(text='⬅️⬅️⬅️',
                                       callback_data=f"seller_open_goods_{goods_categories_id}_{prev_id}"),
            types.InlineKeyboardButton(text=f'{offset + 1}/{goods_count}', callback_data="None"),
            types.InlineKeyboardButton(text='➡️➡️➡️',
                                       callback_data=f"seller_open_goods_{goods_categories_id}_{next_id}")
        ])
    if goods['status'] == 'active':
        buttons.append([types.InlineKeyboardButton(text=f'Деактивировать',
                                                   callback_data=f"seller_deactivate_goods_{goods['id']}"),
                        types.InlineKeyboardButton(text=f'{activ_goods}/{allow_publications}',
                                                   callback_data="None")
                        ])
    else:
        buttons.append([types.InlineKeyboardButton(text=f'Активировать',
                                                   callback_data=f"seller_activate_goods_{goods['id']}"),
                        types.InlineKeyboardButton(text=f'{activ_goods}/{allow_publications}',
                                                   callback_data="None")
                        ])

    buttons.append(
        [types.InlineKeyboardButton(text='Изменить фото', callback_data=f"seller_change_photo_{goods['id']}"),
         types.InlineKeyboardButton(text='Изменить описание',
                                    callback_data=f"seller_change_description_{goods['id']}"),
         ]
    )

    buttons.append([types.InlineKeyboardButton(text='Создать новый товар', callback_data='seller_create_goods')])
    buttons.append(
        [types.InlineKeyboardButton(text='Назад', callback_data=f'seller_open_pod_cat_{pod_categories_id}')])
    buttons.append([types.InlineKeyboardButton(text='На главную', callback_data=f'seller_panel')])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data == 'seller_my_goods')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Категории: ',
                                reply_markup=categories_kb(callback.message.chat.id))


@router.callback_query(F.data.startswith('seller_open_cat_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    categories_id = int(callback.data.split('_')[3])
    await state.update_data({'seller_open_cat': categories_id})
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Подкатегории: ',
                                reply_markup=pod_categories_kb(categories_id, callback.message.chat.id))


@router.callback_query(F.data.startswith('seller_open_pod_cat_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    goods_cat_id = int(callback.data.split('_')[4])
    await state.update_data({'seller_open_pod_cat': goods_cat_id})

    if callback.message.photo:
        msg = await bot.send_message(callback.message.chat.id, text='Товары: ',
                                     reply_markup=pod_pod_categories_kb(goods_cat_id, data['seller_open_cat'],
                                                                        callback.message.chat.id))
        await bot.delete_message(callback.message.chat.id, data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})
    else:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                    text='Товары: ',
                                    reply_markup=pod_pod_categories_kb(goods_cat_id, data['seller_open_cat'],
                                                                       callback.message.chat.id))


@router.callback_query(F.data.startswith('seller_open_goods_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    goods_categories_id = int(callback.data.split('_')[3])
    offset = int(callback.data.split('_')[4]) if callback.data.split('_')[4] else 0
    await state.update_data({'goods_category': goods_categories_id, 'goods_offset': offset})
    await open_goods(callback.message.chat.id, state, bot)


async def open_goods(chat_id, state, bot):
    data = await state.get_data()
    goods = db.get_goods_by_category(data['goods_category'], data['goods_offset'], seller_id=chat_id)
    if goods['goods_count'] == 0:
        await bot.edit_message_text(chat_id=chat_id, message_id=data['msg_id'],
                                    text='В этой категории у вас не товаров',
                                    reply_markup=zero_goods_kb(data['seller_open_pod_cat']))
        return

    activ_goods = db.get_active_goods_count(chat_id)

    allow_publications = db.get_seller_info(chat_id)[0]['publications']

    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'

    text += f"\nОписание: \n\n{goods['description']}\n"

    try:
        await bot.edit_message_media(chat_id=chat_id, message_id=data['msg_id'],
                                     media=InputMediaPhoto(media=goods['photo'], caption=text),
                                     reply_markup=goods_kb(data['goods_offset'], goods, data['goods_category'],
                                                           data['seller_open_pod_cat'], activ_goods,
                                                           allow_publications))
    except:
        msg = await bot.send_photo(chat_id=chat_id, photo=goods['photo'], caption=text,
                                   reply_markup=goods_kb(data['goods_offset'], goods, data['goods_category'],
                                                         data['seller_open_pod_cat'], activ_goods, allow_publications))
        await bot.delete_message(chat_id=chat_id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})


async def update_goods_status(callback: types.CallbackQuery, state: FSMContext, bot: Bot, new_status: str):
    goods_id = int(callback.data.split('_')[3])
    data = await state.get_data()
    db.update_goods(goods_id, status=new_status)
    await open_goods(callback.message.chat.id, state, bot)


@router.callback_query(F.data.startswith('seller_activate_goods_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    allow_publications = db.get_seller_info(callback.message.chat.id)[0]['publications']
    activ_goods = db.get_active_goods_count(callback.message.chat.id)
    if activ_goods >= allow_publications:
        await callback.answer('Вы достигли лимита активированных товаров!\nУлучшите ваш тариф что бы увеличить лимит!',
                              show_alert=True)
        return

    await update_goods_status(callback, state, bot, 'active')


@router.callback_query(F.data.startswith('seller_deactivate_goods_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await update_goods_status(callback, state, bot, 'disable')


@router.callback_query(F.data.startswith('seller_change_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    t = callback.data.split('_')[2]
    i = int(callback.data.split('_')[3])

    await state.update_data({'change_id': i})

    g = {
        'photo': [change.photo, 'Пришлите новое фото:'],
        'description': [change.description, 'Введите новое описание:'],
        'height': [change.height, 'Введите новую высоту товара(в формате от 0 до 12 метров):'],
        'count': [change.count, 'Введите новое количество товара:'],
        'price': [change.price, 'Введите новую цену в Российских рублях']
    }
    data = await state.get_data()
    goods_name = data['goods_category']
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data=f'seller_open_goods_{goods_name}_')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await bot.send_message(chat_id=callback.message.chat.id, text=g[t][1],
                                 reply_markup=keyboard)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])
    await state.update_data({'msg_id': msg.message_id})

    await state.set_state(g[t][0])


@router.message(StateFilter(change.photo))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.photo:
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, photo=message.photo[-1].file_id)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(seller.main)


@router.message(StateFilter(change.description))
async def update_description(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, description=message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(seller.main)


@router.message(StateFilter(change.height))
async def update_height(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, height=message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(seller.main)


@router.message(StateFilter(change.price))
async def update_price(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text or not message.text.isdigit():
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, price=message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(seller.main)


@router.message(StateFilter(change.count))
async def update_count(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text or not message.text.isdigit():
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, count=message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(seller.main)
