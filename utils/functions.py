import datetime

from sqlalchemy import func

from .models import *


def get_categories_main_catalog(offset=0, limit=1):
    with session:
        query = select(Category).offset(offset).limit(limit)
        result = session.execute(query)
        categories = [{'id': row.id, 'name': row.name} for row in result.scalars().all()][0]
        pod_categories_query = session.query(PodCategory).filter(PodCategory.categories == categories['id']).all()
        categories_count = session.query(Category).count()
        categories['categories_count'] = categories_count
        categories['pod_categories'] = []
        ttt = []
        for pc in pod_categories_query:
            count = 0
            gg = get_pod_categories_main_catalog(pc.id)
            if len(gg['goods_categories']) > 0:
                for g in gg['goods_categories']:
                    count += g['count']
            categories['pod_categories'].append({'id': pc.id, 'name': pc.name, 'count': count})
        return categories


def get_admins():
    with session:
        admins = session.query(Admin.id).all()
        return [admin[0] for admin in admins]


def get_support():
    with session:
        support_query = session.query(Support.name, Support.username).all()
        return {name: username for name, username in support_query}


def get_pod_categories(category_id):
    with session:
        pod_categories_query = session.query(PodCategory).filter(PodCategory.categories == category_id).all()
        return [{'id': pc.id, 'name': pc.name} for pc in pod_categories_query]


def get_pod_categories_main_catalog(pod_category_id):
    with session:
        pod_categories_query = session.query(PodCategory).filter(PodCategory.id == pod_category_id).all()
        goods_categories = session.query(GoodsCategory).filter(GoodsCategory.pod_categories == pod_category_id)
        if len(pod_categories_query) == 0:
            return []
        pod_category = [{'id': pc.id, 'name': pc.name} for pc in pod_categories_query][0]
        pod_category['goods_categories'] = [
            {'id': g.id, 'name': g.name, 'count': get_goods_by_category(g.id, status='active')['goods_count']} for g in
            goods_categories]
        return pod_category


def get_goods_categories(pod_category_id):
    with session:
        query = select(GoodsCategory).where(GoodsCategory.pod_categories == pod_category_id)
        goods_categories_result = session.execute(query).scalars().all()
        goods_categories = [{'id': gc.id, 'name': gc.name} for gc in goods_categories_result]
        return goods_categories


def get_goods_by_category(goods_category_id, offset=0, limit=1, status=None, seller_id=None):
    with session:
        total_goods_query = select(func.count()).select_from(Goods).where(Goods.goods_category == goods_category_id)
        if status:
            total_goods_query = total_goods_query.where(Goods.status == status)
        if seller_id:
            total_goods_query = total_goods_query.where(Goods.seller == seller_id)

        total_goods = session.execute(total_goods_query).scalar()

        cyclic_offset = offset % total_goods if total_goods > 0 else 0

        query = select(
            Goods.id,
            Goods.description,
            Goods.photo,
            Goods.height,
            Goods.price,
            Goods.count,
            GoodsCategory.name.label("goods_category_name"),
            Seller.name.label("seller_name"),
            Seller.rating.label("seller_rating"),
            Seller.inn.label("seller_inn"),
            Goods.status,
            Goods.rating
        ).join(
            GoodsCategory, GoodsCategory.id == Goods.goods_category
        ).join(
            Seller, Seller.user_id == Goods.seller
        ).where(
            Goods.goods_category == goods_category_id
        )

        if status:
            query = query.where(Goods.status == status)
        if seller_id:
            query = query.where(Goods.seller == seller_id)

        query = query.offset(cyclic_offset).limit(limit)

        goods_result = session.execute(query).all()

        if not goods_result:
            return {'goods_count': 0, 'goods': []}

        goods = [{
            'id': item[0],
            'description': item[1],
            'photo': item[2],
            'height': item[3],
            'price': item[4],
            'count': item[5],
            'goods_category': item[6],
            'seller': item[7],
            'seller_rating': item[8],
            'seller_inn': item[9],
            'status': item[10],
            'rating': item[11],
            'goods_count': total_goods,
        } for item in goods_result][0]

        return goods


def get_active_goods_count(seller_id):
    with session:
        active_goods_count = session.query(func.count(Goods.id)). \
            filter(Goods.seller == seller_id). \
            filter(Goods.status == 'active'). \
            scalar()
        return active_goods_count


def get_goods_by_id(goods_id):
    with session:
        query = select(
            Goods.id,
            Goods.description,
            Goods.photo,
            Goods.height,
            Goods.price,
            Goods.count,
            GoodsCategory.name.label("goods_category_name"),
            Seller.name.label("seller_name"),
            Seller.rating.label("seller_rating"),
            Seller.inn.label("seller_inn"),
            Goods.status,
            Goods.rating,
            Goods.seller
        ).join(
            GoodsCategory, GoodsCategory.id == Goods.goods_category
        ).join(
            Seller, Seller.user_id == Goods.seller
        ).where(
            Goods.id == goods_id
        )

        goods_result = session.execute(query).first()

        if goods_result is None:
            return None

        goods = {
            'id': goods_result[0],
            'description': goods_result[1],
            'photo': goods_result[2],
            'height': goods_result[3],
            'price': goods_result[4],
            'count': goods_result[5],
            'goods_category': goods_result[6],
            'seller': goods_result[7],
            'seller_rating': goods_result[8],
            'seller_inn': goods_result[9],
            'status': goods_result[10],
            'rating': goods_result[11],
            'seller_id': goods_result[12],

        }

        return goods


def get_seller_info(user_id=None):
    with session:
        query = session.query(
            Seller.name,
            Seller.user_id,
            Seller.balance,
            Seller.phone,
            Tarif.name.label('tarif_name'),
            Seller.tarif_end,
            Seller.status,
            Seller.rating,
            Tarif.publications
        ).join(
            Tarif, Seller.tarif == Tarif.id
        )

        if user_id is not None:
            query = query.filter(Seller.user_id == user_id)

        sellers_info = query.all()

        results = []
        for seller_info in sellers_info:
            results.append({
                'name': seller_info.name,
                'user_id': seller_info.user_id,
                'balance': seller_info.balance,
                'phone': seller_info.phone,
                'tarif_name': seller_info.tarif_name,
                'tarif_end': seller_info.tarif_end,
                'status': seller_info.status,
                'rating': seller_info.rating,
                'publications': seller_info.publications,
            })

        return results if results else None


def add_balance(user_id, amount):
    with session:
        seller = session.query(Seller).filter(Seller.user_id == user_id).first()
        if seller:
            seller.balance += amount
            session.commit()


def rem_balance(user_id, amount):
    with session:
        seller = session.query(Seller).filter(Seller.user_id == user_id).first()
        if seller:
            seller.balance -= amount
            session.commit()


def add_payment(payment_id, user_id, amount):
    with session:
        new_payment = Payment(payments_id=payment_id, user_id=user_id, amount=amount)
        session.add(new_payment)
        session.commit()


def get_tarifs():
    with session:
        rows = session.query(Tarif).all()

        tarifs = {}
        for row in rows:
            tarifs[row.name] = {
                'id': row.id,
                'amount': row.amount,
                'days': row.days,
                'publications': row.publications,
            }

        return tarifs


def update_tarif(tarif_name, **kwargs):
    tarif = session.query(Tarif).filter(Tarif.name == tarif_name).first()
    if tarif:
        for key, value in kwargs.items():
            if hasattr(tarif, key):
                setattr(tarif, key, value)
        session.commit()


def update_seller(user_id, updates):
    with session:
        seller = session.query(Seller).filter(Seller.user_id == user_id).first()
        if seller:
            for key, value in updates.items():
                if hasattr(seller, key):
                    setattr(seller, key, value)
            session.commit()


def check_seller_exists(user_id):
    with session:
        seller = session.query(Seller).filter(Seller.user_id == user_id).first()
        return seller is not None


def get_request(user_id):
    with session:
        request = session.query(Request).filter(Request.user_id == user_id).first()

        if request is None:
            return None

        request_dict = {
            'id': request.id,
            'seller_type': request.seller_type,
            'name': request.name,
            'fio': request.fio,
            'document_type': request.document_type,
            'file_id': request.file_id,
            'user_id': request.user_id,
            'phone': request.phone,
            'status': request.status,
            'comment': request.comment,
            'inn': request.inn,
        }
        return request_dict


def get_requests(status=None, offset=0, limit=1):
    with session:
        query = session.query(Request)

        if status is not None:
            query = query.filter(Request.status == status)

        total_count = query.count()

        requests = session.execute(query).first()
        if requests is None:
            return None
        result = [
            {
                'id': request.id,
                'seller_type': request.seller_type,
                'name': request.name,
                'fio': request.fio,
                'document_type': request.document_type,
                'file_id': request.file_id,
                'user_id': request.user_id,
                'phone': request.phone,
                'status': request.status,
                'comment': request.comment,
                'total_count': total_count,
                'inn': request.inn
            } for request in requests
        ]

        return result[0]


def update_request(request_id, **kwargs):
    with session:
        request = session.query(Request).filter(Request.id == request_id).first()
        if request:
            for key, value in kwargs.items():
                if hasattr(request, key):
                    setattr(request, key, value)
            session.commit()


def create_order(buy, seller, user_id, goods_id):
    with session:
        new_order = Order(buy=buy, seller=seller, status='active', user_id=user_id, goods_id=goods_id,
                          date=datetime.datetime.now())
        session.add(new_order)
        session.commit()


def get_orders_by_user(seller_id=None, user_id=None, status=None, date_filter=None, offset=0, page_size=1):
    with session:
        base_query = select(
            Order.id.label("order_id"),
            Order.buy,
            Order.status,
            Order.user_id,
            Order.goods_id,
            Order.date,
            Seller.name.label("seller_name")
        ).join(
            Seller, Order.seller == Seller.user_id
        )

        if seller_id is not None:
            base_query = base_query.where(Order.seller == seller_id)
        if user_id is not None:
            base_query = base_query.where(Order.user_id == user_id)
        if status is not None:
            base_query = base_query.where(Order.status == status)

        if date_filter == 'today':
            today = datetime.datetime.now().date()
            base_query = base_query.where(func.date(Order.date) == today)
        elif date_filter == 'month':
            current_year = datetime.datetime.now().year
            current_month = datetime.datetime.now().month
            base_query = base_query.where(func.extract('year', Order.date) == current_year,
                                          func.extract('month', Order.date) == current_month)

        base_query = base_query.order_by(Order.id.desc())

        total_count = session.execute(select(func.count()).select_from(base_query.subquery())).scalar()

        paginated_query = base_query.offset(offset).limit(page_size)
        orders = session.execute(paginated_query).fetchall()

        if len(orders) == 0:
            return [{'orders_count': total_count}]

        result = [{
            'order_id': order.order_id,
            'buy': order.buy,
            'status': order.status,
            'user_id': order.user_id,
            'seller_name': order.seller_name,
            'goods_id': order.goods_id,
            'date': order.date,
            'orders_count': total_count
        } for order in orders]

        return result


def get_all_categories():
    with session:
        categories_query = session.query(Category).all()
        categories = [{'id': category.id, 'name': category.name} for category in categories_query]
        return categories


def get_all_categories_seller(user_id):
    with session:
        categories_query = session.query(Category).all()
        categories = []
        for category in categories_query:
            p_cat = get_all_pod_categories(category.id, user_id)
            count = sum([x['count'] for x in p_cat])
            categories.append({'id': category.id, 'name': category.name, 'count': count})
        return categories


def get_all_pod_categories(category_id, user_id):
    with session:
        subcategories_query = session.query(PodCategory).filter(PodCategory.categories == category_id).all()
        subcategories = []
        for subcategory in subcategories_query:
            g_cat = get_all_goods_categories(subcategory.id, user_id)
            count = sum([x['count'] for x in g_cat])
            subcategories.append({'id': subcategory.id, 'name': subcategory.name, 'count': count})
        return subcategories


def get_all_goods_categories(pod_category_id, user_id):
    with session:
        goods_categories_query = session.query(GoodsCategory).filter(
            GoodsCategory.pod_categories == pod_category_id).all()

        goods_categories_query = [{'id': subcategory.id, 'name': subcategory.name,
                                   'count': get_goods_by_category(subcategory.id, seller_id=user_id)['goods_count']} for
                                  subcategory in
                                  goods_categories_query]
        return goods_categories_query


def create_goods(description, photo, height, price, count, category_id, seller_id, status):
    with session:
        new_goods = Goods(
            description=description,
            photo=photo,
            height=height,
            price=price,
            count=count,
            goods_category=category_id,
            seller=seller_id,
            status=status
        )
        session.add(new_goods)
        session.commit()


def update_goods(goods_id, **kwargs):
    with session:
        goods = session.query(Goods).filter(Goods.id == goods_id).first()
        if goods:
            for key, value in kwargs.items():
                if hasattr(goods, key):
                    setattr(goods, key, value)
            session.commit()
            return True
        else:
            return False


def update_goods_status_by_seller(seller_id, new_status):
    with session:
        t = session.query(Goods).filter(Goods.seller == seller_id).update({"status": new_status})
        print(session.query(Goods).filter(Goods.seller == seller_id))
        session.commit()


def add_basket(user_id, goods_id, count):
    with session:
        new_basket = Basket(user_id=user_id, goods=goods_id, count=count)
        session.add(new_basket)
        session.commit()


def get_basket(user_id, offset=0, limit=1):
    with session:
        records = session.query(Basket).filter_by(user_id=user_id).offset(offset).limit(limit).all()
        total_count = session.query(Basket).filter_by(user_id=user_id).count()
        result = [{
            'id': record.id,
            'goods': get_goods_by_id(record.goods),
            'count': record.count,
            'basket_count': total_count
        } for record in records]
        if len(result) == 0:
            return [{'basket_count': total_count}]
        return result


def update_basket_record(basket_id, new_count):
    with session:
        basket_record = session.query(Basket).filter_by(id=basket_id).first()
        if basket_record:
            basket_record.count = new_count
            session.commit()


def delete_basket_by_id(basket_id):
    with session:
        basket_record = session.query(Basket).filter(Basket.id == basket_id).first()
        if basket_record:
            session.delete(basket_record)
            session.commit()


def create_request(seller_type, name, fio, document_type, file_id, user_id, phone, status, comment, inn):
    with session:
        new_request = Request(
            seller_type=seller_type,
            name=name,
            fio=fio,
            document_type=document_type,
            file_id=file_id,
            user_id=user_id,
            phone=phone,
            status=status,
            comment=comment,
            inn=inn,
        )

        session.add(new_request)
        session.commit()


def create_review(goods_id, comment, photo_doc, photo_goods):
    with session:
        new_review = Review(goods=goods_id, comment=comment, photo_doc=photo_doc, photo_goods=photo_goods)
        session.add(new_review)
        session.commit()


def delete_review(review_id):
    with session:
        review = session.query(Review).filter(Review.id == review_id).first()
        if review:
            session.delete(review)
            session.commit()


def get_reviews_with_offset(offset=0, limit=1):
    total_count = session.query(Review).count()

    reviews = session.query(Review).offset(offset).limit(limit).all()

    reviews_data = [
        {
            'id': review.id,
            'goods': review.goods,
            'comment': review.comment,
            'photo_doc': review.photo_doc,
            'photo_goods': review.photo_goods
        }
        for review in reviews
    ]

    return {
        'total_count': total_count,
        'reviews': reviews_data
    }


def update_category_name(category_id, new_name):
    with session:
        category = session.query(Category).filter(Category.id == category_id).first()
        if category:
            category.name = new_name
            session.commit()


def update_pod_category_name(pod_category_id, new_name):
    with session:
        pod_category = session.query(PodCategory).filter(PodCategory.id == pod_category_id).first()
        if pod_category:
            pod_category.name = new_name
            session.commit()


def create_category(name):
    with session:
        new_category = Category(name=name)
        session.add(new_category)
        session.commit()


def create_pod_category(name, category_id):
    with session:
        new_pod_category = PodCategory(name=name, categories=category_id)
        session.add(new_pod_category)
        session.commit()


def update_goods_category_name(category_id, new_name):
    with session:
        goods_category = session.query(GoodsCategory).filter(GoodsCategory.id == category_id).first()
        if goods_category:
            goods_category.name = new_name
            session.commit()


def create_goods_category(name, pod_category_id):
    new_goods_category = GoodsCategory(name=name, pod_categories=pod_category_id)
    session.add(new_goods_category)
    session.commit()


def update_seller_rating_by_goods_id(goods_id, new_rating):
    goods = session.query(Goods).filter(Goods.id == goods_id).first()
    if goods:
        seller = session.query(Seller).filter(Seller.user_id == goods.seller).first()
        if seller:
            seller.rating = new_rating
            session.commit()


def create_seller(name, user_id, balance, phone, tarif, tarif_end, status, rating, inn):
    new_seller = Seller(name=name, user_id=user_id, balance=balance, phone=phone,
                        tarif=tarif, tarif_end=tarif_end, status=status, rating=rating, inn=inn)
    session.add(new_seller)
    session.commit()


def add_ban_record(ban_text: str) -> None:
    with session:
        new_record = BanList(text=ban_text)
        session.add(new_record)
        session.commit()


def get_ban_records_with_offset(limit: int, offset: int) -> tuple:
    with session:
        total_records = session.query(BanList).count()
        records = session.query(BanList).offset(offset).limit(limit).all()
        result = [x.text for x in records]
        return total_records, result
