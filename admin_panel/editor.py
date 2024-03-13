from aiogram import Router, types, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto

from admin_panel.main_menu import admin
from utils import models as db

router = Router()


class editor(StatesGroup):
    main = State()
    edit_cat = State()
    create_cat = State()
    edit_pod_cat = State()
    create_pod_cat = State()
    edit_goods_cat = State()
    create_goods_cat = State()
    change_photo = State()
    change_description = State()
    change_height = State()
    change_count = State()
    change_price = State()
    change_goods_rating = State()
    change_seller_rating = State()


def categories_kb():
    buttons = []

    categories = db.get_all_categories()

    for cat in categories:
        buttons.append([
            types.InlineKeyboardButton(text=cat['name'], callback_data=f"open_cat_{cat['id']}_up"),
            types.InlineKeyboardButton(text='ред', callback_data=f"edit_cat_{cat['id']}")
        ])
    buttons.append([types.InlineKeyboardButton(text='Создать новую', callback_data='create_cat')])
    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data='admin_panel')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def pod_categories_kb(cat_id):
    pod_categories = db.get_pod_categories(cat_id)
    buttons = []

    for pod_cat in pod_categories:
        buttons.append([
            types.InlineKeyboardButton(text=pod_cat['name'], callback_data=f"open_pod_cat_{pod_cat['id']}"),
            types.InlineKeyboardButton(text='ред', callback_data=f"edit_pod_cat_{pod_cat['id']}")
        ])
    buttons.append([types.InlineKeyboardButton(text='Создать новую', callback_data='create_pod_cat')])
    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data='start_edit')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def goods_categories_kb(pod_categories_id, cat_id):
    goods_categories = db.get_goods_categories(pod_categories_id)
    buttons = []
    for goods_cat in goods_categories:
        buttons.append([
            types.InlineKeyboardButton(text=goods_cat['name'], callback_data=f"open_goods_{goods_cat['id']}_0"),
            types.InlineKeyboardButton(text='ред', callback_data=f"edit_goods_cat_{goods_cat['id']}")
        ])
    buttons.append([types.InlineKeyboardButton(text='Создать новую', callback_data='create_goods_cat')])
    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data=f'open_cat_{cat_id}')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def goods_kb(offset, goods, goods_categories_id, pod_categories_id):
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
                                       callback_data=f"open_goods_{goods_categories_id}_{prev_id}"),
            types.InlineKeyboardButton(text=f'{offset + 1}/{goods_count}', callback_data="None"),
            types.InlineKeyboardButton(text='➡️➡️➡️',
                                       callback_data=f"open_goods_{goods_categories_id}_{next_id}")
        ])

    if goods['status'] == 'active':
        buttons.append([types.InlineKeyboardButton(text=f'Деактивировать',
                                                   callback_data=f"deactivate_goods_{goods['id']}"),
                        types.InlineKeyboardButton(text='Изменить фото',
                                                   callback_data=f"change_photo_{goods['id']}")
                        ])
    else:
        buttons.append([types.InlineKeyboardButton(text=f'Активировать',
                                                   callback_data=f"activate_goods_{goods['id']}"),
                        types.InlineKeyboardButton(text='Изменить фото',
                                                   callback_data=f"change_photo_{goods['id']}")
                        ])

    buttons.append(
        [
            types.InlineKeyboardButton(text='Рейтинг товара',
                                       callback_data=f"change_goods+rating_{goods['id']}"),
            types.InlineKeyboardButton(text='Рейтинг продавца', callback_data=f"change_seller+rating_{goods['id']}")
        ]
    )

    buttons.append(
        [
            types.InlineKeyboardButton(text='Описание',
                                       callback_data=f"change_description_{goods['id']}"),
        ]
    )

    buttons.append(
        [types.InlineKeyboardButton(text='Назад', callback_data=f'open_pod_cat_{pod_categories_id}')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def cansel_kb():
    buttons = [
        [types.InlineKeyboardButton(text='Отмена', callback_data='cansel')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data.startswith('start_edit'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Категории:',
                                reply_markup=categories_kb())


@router.callback_query(F.data.startswith('open_cat_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    cat_id = int(callback.data.split('_')[2])
    await state.update_data({'open_cat': cat_id})
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Подкатегории:',
                                reply_markup=pod_categories_kb(cat_id))


@router.callback_query(F.data.startswith('open_pod_cat_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    pod_cat_id = int(callback.data.split('_')[3])
    await state.update_data({'open_pod_cat': pod_cat_id})
    if callback.message.photo:
        msg = await bot.send_message(chat_id=callback.message.chat.id, text='Подкатегории:',
                                     reply_markup=goods_categories_kb(pod_cat_id, data['open_cat']))
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})
    else:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                    text='Категории товаров:',
                                    reply_markup=goods_categories_kb(pod_cat_id, data['open_cat']))


@router.callback_query(F.data.startswith('open_goods_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    goods_cat_id = int(callback.data.split('_')[2])
    offset = int(callback.data.split('_')[3])
    await state.update_data({'open_goods_cat': goods_cat_id, 'open_goods_offset': offset})
    await open_goods(callback.message.chat.id, state, bot)


async def open_goods(chat_id, state, bot):
    data = await state.get_data()
    goods = db.get_goods_by_category(data['open_goods_cat'], data['open_goods_offset'])
    if goods['goods_count'] == 0:
        buttons = [
            [types.InlineKeyboardButton(text='Назад', callback_data=f"open_pod_cat_{data['open_pod_cat']}")],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.edit_message_text(chat_id=chat_id, message_id=data['msg_id'],
                                    text='В этой категории нет товаров',
                                    reply_markup=keyboard)
        return

    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'
    text += f"Инн поставщика: `" + (str(goods['seller_inn'])) + '`\n'

    text += f"\nОписание: \n\n{goods['description']}\n"

    try:
        await bot.edit_message_media(chat_id=chat_id, message_id=data['msg_id'],
                                     media=InputMediaPhoto(media=goods['photo'], caption=text, parse_mode="MARKDOWN"),
                                     reply_markup=goods_kb(data['open_goods_offset'], goods, data['open_goods_cat'],
                                                           data['open_pod_cat']))
    except:
        msg = await bot.send_photo(chat_id=chat_id, photo=goods['photo'], caption=text,parse_mode="MARKDOWN",
                                   reply_markup=goods_kb(data['open_goods_offset'], goods, data['open_goods_cat'],
                                                         data['open_pod_cat']))
        await bot.delete_message(chat_id=chat_id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})


@router.callback_query(F.data.startswith('edit_cat_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    cat_id = int(callback.data.split('_')[2])
    await state.update_data({'edit_cat': cat_id})
    await state.set_state(editor.edit_cat)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите новое имя для данной категории:',
                                reply_markup=cansel_kb())


@router.message(StateFilter(editor.edit_cat))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return
    db.update_category_name(data['edit_cat'], message.text)
    await state.set_state(editor.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Категории:',
                                reply_markup=categories_kb())


@router.callback_query(F.data == 'cansel', StateFilter(editor.edit_cat, editor.create_cat))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(editor.main)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Категории:',
                                reply_markup=categories_kb())


@router.callback_query(F.data.startswith('create_cat'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(editor.create_cat)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите имя новой категории:',
                                reply_markup=cansel_kb())


@router.message(StateFilter(editor.create_cat))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return
    db.create_category(message.text)
    await state.set_state(editor.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Категории:',
                                reply_markup=categories_kb())


@router.callback_query(F.data.startswith('edit_pod_cat_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    cat_id = int(callback.data.split('_')[3])
    await state.update_data({'edit_pod_cat': cat_id})
    await state.set_state(editor.edit_pod_cat)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите новое имя для данной подкатегории:',
                                reply_markup=cansel_kb())


@router.message(StateFilter(editor.edit_pod_cat))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return
    db.update_pod_category_name(data['edit_pod_cat'], message.text)
    await state.set_state(editor.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Подкатегории:',
                                reply_markup=pod_categories_kb(data['open_cat']))


@router.callback_query(F.data == 'cansel', StateFilter(editor.edit_pod_cat, editor.create_pod_cat))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(editor.main)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Подкатегории:',
                                reply_markup=pod_categories_kb(data['open_cat']))


@router.callback_query(F.data.startswith('create_pod_cat'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(editor.create_pod_cat)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите имя новой подкатегории:',
                                reply_markup=cansel_kb())


@router.message(StateFilter(editor.create_pod_cat))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return
    db.create_pod_category(message.text, data['open_cat'])
    await state.set_state(editor.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Подкатегории:',
                                reply_markup=pod_categories_kb(data['open_cat']))


@router.callback_query(F.data.startswith('edit_goods_cat_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    goods_id = int(callback.data.split('_')[3])
    await state.update_data({'edit_goods_cat': goods_id})
    await state.set_state(editor.edit_goods_cat)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите новое имя для данной категории товаров:',
                                reply_markup=cansel_kb())


@router.message(StateFilter(editor.edit_goods_cat))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return
    db.update_goods_category_name(data['edit_goods_cat'], message.text)
    await state.set_state(editor.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Категории товаров:',
                                reply_markup=goods_categories_kb(data['open_pod_cat'], data['open_cat']))


@router.callback_query(F.data == 'cansel', StateFilter(editor.edit_goods_cat, editor.create_goods_cat))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(editor.main)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text='Категории товаров:',
                                reply_markup=goods_categories_kb(data['open_pod_cat'], data['open_cat']))


@router.callback_query(F.data.startswith('create_goods_cat'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(editor.create_goods_cat)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                text=f'Введите имя новой категории товара:',
                                reply_markup=cansel_kb())


@router.message(StateFilter(editor.create_goods_cat))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await message.delete()
    if not message.text:
        return
    db.create_goods_category(message.text, data['open_pod_cat'])
    await state.set_state(editor.main)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'],
                                text='Категории товаров:',
                                reply_markup=goods_categories_kb(data['open_pod_cat'], data['open_cat']))


async def update_goods_status(callback: types.CallbackQuery, state: FSMContext, bot: Bot, new_status: str):
    goods_id = int(callback.data.split('_')[2])
    data = await state.get_data()
    db.update_goods(goods_id, status=new_status)
    await open_goods(callback.message.chat.id, state, bot)


@router.callback_query(F.data.startswith('activate_goods_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await update_goods_status(callback, state, bot, 'active')


@router.callback_query(F.data.startswith('deactivate_goods_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await update_goods_status(callback, state, bot, 'disable')


@router.callback_query(F.data.startswith('change_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    t = callback.data.split('_')[1]
    i = int(callback.data.split('_')[2])

    await state.update_data({'change_id': i})

    g = {
        'photo': [editor.change_photo, 'Пришлите новое фото:'],
        'description': [editor.change_description, 'Введите новое описание:'],
        'height': [editor.change_height, 'Введите новую высоту товара(в формате от 0 до 12 метров):'],
        'count': [editor.change_count, 'Введите новое количество товара:'],
        'price': [editor.change_price, 'Введите новую цену в Российских рублях'],
        'goods+rating': [editor.change_goods_rating, 'Введите новый рейтинг товара'],
        'seller+rating': [editor.change_seller_rating, 'Введите новый рейтинг поставщика'],
    }
    data = await state.get_data()
    goods_cat_id = data['goods_category']
    buttons = [
        [types.InlineKeyboardButton(text='Отмена',
                                    callback_data=f"open_goods_{goods_cat_id}_{data['open_goods_offset']}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await bot.send_message(chat_id=callback.message.chat.id, text=g[t][1],
                                 reply_markup=keyboard)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])
    await state.update_data({'msg_id': msg.message_id})

    await state.set_state(g[t][0])


@router.message(StateFilter(editor.change_photo))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.photo:
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, photo=message.photo[-1].file_id)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(admin.main)


@router.message(StateFilter(editor.change_description))
async def update_description(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, description=message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(admin.main)


@router.message(StateFilter(editor.change_height))
async def update_height(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, height=message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(admin.main)


@router.message(StateFilter(editor.change_price))
async def update_price(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text or not message.text.isdigit():
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, price=message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(admin.main)


@router.message(StateFilter(editor.change_count))
async def update_count(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text or not message.text.isdigit():
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, count=message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(admin.main)


@router.message(StateFilter(editor.change_goods_rating))
async def update_count(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    try:
        float(message.text)
    except ValueError:
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_goods(goods_id, rating=message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(admin.main)


@router.message(StateFilter(editor.change_seller_rating))
async def update_count(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()
    if not message.text:
        return
    try:
        float(message.text)
    except ValueError:
        return
    data = await state.get_data()
    goods_id = data['change_id']
    db.update_seller_rating_by_goods_id(goods_id, message.text)
    await open_goods(message.chat.id, state, bot)
    await state.set_state(admin.main)
