import asyncio
import datetime
import logging
import threading
import time

from aiogram import Bot, Dispatcher

from utils.storage import SQLiteStorage

import user_panel.main_catalog
import user_panel.support
import user_panel.create_order
import user_panel.put_to_basket
import user_panel.my_basket
import user_panel.my_buy
import user_panel.create_reviews
import user_panel.ban_list

import admin_panel.main_menu
import admin_panel.editor
import admin_panel.requests_moderation
import admin_panel.edit_tarifs
import admin_panel.ban_seller
import admin_panel.all_orders
import admin_panel.reviews_moderation
import admin_panel.add_ban_list

import seller_panel.main_menu
import seller_panel.registration
import seller_panel.balance
import seller_panel.tarif
import seller_panel.my_goods
import seller_panel.create_goods
import seller_panel.my_orders

from utils import models as db

token = ""
bot = Bot(token=token)
dp = Dispatcher(storage=SQLiteStorage())


async def tarif_worker():
    sellers = db.get_seller_info()
    tarifs = db.get_tarifs()

    for seller in sellers:
        tarif_name = seller['tarif_name']
        if tarif_name == 'FREE':
            continue
        ost_days = (datetime.datetime.strptime(seller['tarif_end'],
                                               '%Y-%m-%d %H:%M:%S.%f') - datetime.datetime.now()).days
        if ost_days == 3:
            await bot.send_message(seller['user_id'],
                                   f'Тариф {tarif_name} истекает через 3 дня, убедитесь что на вашем балансе достаточно средст!')
            return
        if ost_days == -1:
            if seller['balance'] < tarifs[tarif_name]['amount']:
                await bot.send_message(seller['user_id'],
                                       f'Тариф {tarif_name} истек, а на вашем балансе недостаточно средст для продления!\nВаш тариф снижен до FREE.')
                db.update_goods_status_by_seller(seller['user_id'], 'disabel')
                return

            await bot.send_message(seller['user_id'],
                                   f'Тариф {tarif_name} продён ещё на месяц!')
            db.rem_balance(seller['user_id'], tarifs.get(tarif_name)['amount'])
            return

    await asyncio.sleep(60 * 60 * 24)
    await tarif_worker()


async def main():
    logging.basicConfig(level=logging.INFO)

    dp.include_routers(user_panel.main_catalog.router, user_panel.support.router, user_panel.create_order.router,
                       user_panel.put_to_basket.router, user_panel.my_basket.router, user_panel.my_buy.router,
                       user_panel.create_reviews.router, user_panel.ban_list.router)
    dp.include_routers(admin_panel.main_menu.router, admin_panel.editor.router, admin_panel.requests_moderation.router,
                       admin_panel.edit_tarifs.router,
                       admin_panel.ban_seller.router, admin_panel.all_orders.router,
                       admin_panel.reviews_moderation.router, admin_panel.add_ban_list.router)
    dp.include_routers(seller_panel.main_menu.router, seller_panel.registration.router, seller_panel.balance.router,
                       seller_panel.tarif.router, seller_panel.my_goods.router, seller_panel.create_goods.router,
                       seller_panel.my_orders.router)

    bot_task = asyncio.create_task(tarif_worker())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

    await bot_task


if __name__ == "__main__":
    asyncio.run(main())
