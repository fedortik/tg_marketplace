from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto

from utils import models as db

router = Router()


class menu(StatesGroup):
    main_catalog = State()


def main_catalog_kb(offset, categories, chat_id, full):
    categories_count = categories['categories_count']
    buttons = []
    if len(categories['pod_categories']) > 18 and not full:
        for i in range(0, 18, 2):
            row_buttons = categories['pod_categories'][i:i + 2]
            buttons.append([
                types.InlineKeyboardButton(text=pod_cat['name'] + f" ({pod_cat['count']})",
                                           callback_data=f"main_pod_{pod_cat['id']}")
                for pod_cat in row_buttons
            ])
        buttons.append([types.InlineKeyboardButton(text="Развернуть", callback_data=f"main_menu_{offset}_full")])
    elif full:
        for i in range(0, len(categories['pod_categories']), 2):
            row_buttons = categories['pod_categories'][i:i + 2]
            buttons.append([
                types.InlineKeyboardButton(text=pod_cat['name'] + f" ({pod_cat['count']})",
                                           callback_data=f"main_pod_{pod_cat['id']}")
                for pod_cat in row_buttons
            ])
        buttons.append([types.InlineKeyboardButton(text="Свернуть", callback_data=f"main_menu_{offset}")])
    else:
        for i in range(0, len(categories['pod_categories']), 2):
            row_buttons = categories['pod_categories'][i:i + 2]
            buttons.append([
                types.InlineKeyboardButton(text=pod_cat['name'] + f" ({pod_cat['count']})",
                                           callback_data=f"main_pod_{pod_cat['id']}")
                for pod_cat in row_buttons
            ])

    prev_offset = (offset - 1) % categories_count
    next_offset = (offset + 1) % categories_count

    navigation_buttons = [
        types.InlineKeyboardButton(text='⬅️⬅️⬅️', callback_data=f"main_menu_{prev_offset}"),
        types.InlineKeyboardButton(text=f'{offset + 1}/{categories_count}', callback_data="None"),
        types.InlineKeyboardButton(text='➡️➡️➡️', callback_data=f"main_menu_{next_offset}")
    ]
    basket = [types.InlineKeyboardButton(text="Моя корзина", callback_data="my_basket_"),
              types.InlineKeyboardButton(text="Мои покупки", callback_data="my_buy_")]
    special_buttons = [
        types.InlineKeyboardButton(text="Для поставщиков", callback_data="seller_panel"),
        types.InlineKeyboardButton(text="Чёрный список", callback_data="ban_list_0"),
    ]
    support = [types.InlineKeyboardButton(text="Поддержка", callback_data="support"), ]

    buttons.append(navigation_buttons)
    buttons.append(basket)

    buttons.append(special_buttons)
    buttons.append(support)

    if chat_id in db.get_admins():
        buttons.append([types.InlineKeyboardButton(text="Админ панель", callback_data="admin_panel")])

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


def goods_kb(offset, goods, goods_categories_id, pod_categories_id):
    buttons = []
    goods_count = goods['goods_count']
    prev_id = (offset - 1) % goods_count
    next_id = (offset + 1) % goods_count

    one_buttons = [
        types.InlineKeyboardButton(text='⬅️⬅️⬅️', callback_data="None"),
        types.InlineKeyboardButton(text=f'{offset + 1}/{goods_count}', callback_data="None"),
        types.InlineKeyboardButton(text='➡️➡️➡️', callback_data="None")
    ]

    navigation_buttons = [
        types.InlineKeyboardButton(text='⬅️⬅️⬅️', callback_data=f"main_goods_{goods_categories_id}_{prev_id}"),
        types.InlineKeyboardButton(text=f'{offset + 1}/{goods_count}', callback_data="None"),
        types.InlineKeyboardButton(text='➡️➡️➡️', callback_data=f"main_goods_{goods_categories_id}_{next_id}")
    ]
    if goods['goods_count'] == 1:
        buttons.append(one_buttons)
    else:
        buttons.append(navigation_buttons)

    action_buttons = [
        types.InlineKeyboardButton(text='Купить', callback_data=f"main_buy_{goods['id']}"),
        types.InlineKeyboardButton(text='Положить в корзину', callback_data=f"main_put_{goods['id']}")
    ]

    buttons.append(action_buttons)

    back_button = [types.InlineKeyboardButton(text='Назад', callback_data=f'main_pod_{pod_categories_id}')]
    buttons.append(back_button)

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    categories = db.get_categories_main_catalog(0)
    try:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['msg_id'], text=categories['name'] + ':',
                                    reply_markup=main_catalog_kb(0, categories, message.chat.id, full=False))
    except:
        msg = await message.answer(categories['name'] + ':',
                                   reply_markup=main_catalog_kb(0, categories, message.chat.id, full=False))
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=data['msg_id'])
        except:
            pass
        await state.set_data({'msg_id': msg.message_id})
    await message.delete()
    await state.set_state(menu.main_catalog)


@router.callback_query(F.data.startswith('main_menu_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    offset = int(callback.data.split('_')[2]) if callback.data.split('_')[2] else data[
        'offset'] if 'offset' in data else 0
    full = True
    try:
        callback.data.split('_')[3]
    except:
        full = False
    await state.update_data({'offset': offset})
    await state.set_state(menu.main_catalog)
    categories = db.get_categories_main_catalog(offset)
    try:
        await bot.edit_message_text(categories['name'] + ':', callback.message.chat.id, data['msg_id'],
                                    reply_markup=main_catalog_kb(offset, categories, callback.message.chat.id, full))
    except:
        msg = await bot.send_message(callback.message.chat.id, categories['name'] + ':',
                                     reply_markup=main_catalog_kb(offset, categories, callback.message.chat.id, full))
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})


@router.callback_query(F.data.startswith('main_pod_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    pod_categories_id = int(callback.data.split('_')[2])
    pod_categories = db.get_pod_categories_main_catalog(pod_categories_id)
    if len(pod_categories) == 0:
        await callback.answer('Данная подкатегория пуста', show_alert=True)
        return

    buttons = []

    for i in range(0, len(pod_categories['goods_categories']), 2):
        row_buttons = pod_categories['goods_categories'][i:i + 2]
        buttons.append([
            types.InlineKeyboardButton(text=g['name'] + f" ({g['count']})", callback_data=f"main_goods_{g['id']}_")
            for g in row_buttons
        ])


    buttons.append([types.InlineKeyboardButton(text='Назад', callback_data=f'main_menu_')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    if not callback.message.photo:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                    text=pod_categories['name'] + ':',
                                    reply_markup=keyboard)
    else:
        msg = await bot.send_message(chat_id=callback.message.chat.id, text=pod_categories['name'] + ':',
                                     reply_markup=keyboard)
        await state.update_data({'msg_id': msg.message_id})
        await callback.message.delete()
    await state.set_state(menu.main_catalog)
    await state.update_data({'open_pod_categories': pod_categories['id']})


@router.callback_query(F.data.startswith('main_goods_'))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    goods_categories_id = int(callback.data.split('_')[2])
    offset = int(callback.data.split('_')[3]) if callback.data.split('_')[3] else 0
    goods = db.get_goods_by_category(goods_categories_id, offset, status='active')
    await state.update_data({'goods_category': goods_categories_id, 'goods_offset': offset})

    if goods['goods_count'] == 0:
        await callback.answer('Данная категория товаров пуста', show_alert=True)
        return
    text = f"Название: {goods['goods_category']}\n"
    text += f'Рейтинг товара: ' + (str(goods['rating']) if goods['rating'] else 'отсутствует') + '\n'
    text += f'Рейтинг поставщика: ' + (str(goods['seller_rating']) if goods['seller_rating'] else 'отсутствует') + '\n'
    text += f"Инн поставщика: `" + (str(goods['seller_inn'])) + '`\n'

    text += f"\nОписание: \n\n{goods['description']}\n"


    if callback.message.photo:
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=data['msg_id'],
                                     media=InputMediaPhoto(media=goods['photo'], caption=text, parse_mode='MARKDOWN'),
                                     reply_markup=goods_kb(offset, goods, goods_categories_id,
                                                           data['open_pod_categories']))
    else:
        msg = await bot.send_photo(chat_id=callback.message.chat.id, photo=goods['photo'], caption=text,
                                   reply_markup=goods_kb(offset, goods, goods_categories_id,
                                                         data['open_pod_categories']), parse_mode="MARKDOWN")
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['msg_id'])
        await state.update_data({'msg_id': msg.message_id})
    await state.set_state(menu.main_catalog)


@router.callback_query(F.data == 'None')
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
