from sqlalchemy import create_engine, Column, Integer, String, select, ForeignKey, Text, REAL, update
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()

sqlite_database = "sqlite:///bd.sqlite"
engine = create_engine(sqlite_database)
session = Session(autoflush=False, bind=engine)


class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)


class Basket(Base):
    __tablename__ = 'baskets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    goods = Column(Integer, ForeignKey('goods.id', ondelete="CASCADE", onupdate="CASCADE"))
    count = Column(Integer)


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)


class Goods(Base):
    __tablename__ = 'goods'
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text)
    photo = Column(Text)
    height = Column(Text)
    price = Column(Text)
    count = Column(Text)
    goods_category = Column(Integer, ForeignKey('goods_categories.id'), nullable=False)
    seller = Column(Integer, ForeignKey('sellers.user_id'), nullable=False)
    status = Column(Text)
    rating = Column(REAL)


class GoodsCategory(Base):
    __tablename__ = 'goods_categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    pod_categories = Column(Integer, ForeignKey('pod_categories.id'), nullable=False)


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    buy = Column(String)
    seller = Column(Integer, ForeignKey('sellers.user_id'))
    status = Column(String)
    user_id = Column(Integer)
    goods_id = Column(Integer, ForeignKey('goods.id'), nullable=False)
    date = Column(Text)


class Payment(Base):
    __tablename__ = 'payments'
    payments_id = Column(Text, primary_key=True)
    user_id = Column(Integer)
    amount = Column(Integer)


class PodCategory(Base):
    __tablename__ = 'pod_categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    categories = Column(Integer, ForeignKey('categories.id'), nullable=False)


class Request(Base):
    __tablename__ = 'requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_type = Column(Text)
    name = Column(Text)
    fio = Column(Text)
    document_type = Column(Text)
    file_id = Column(Text)
    user_id = Column(Integer)
    phone = Column(Text)
    status = Column(Text)
    comment = Column(Text)
    inn = Column(Text)


class Seller(Base):
    __tablename__ = 'sellers'
    name = Column(Text)
    user_id = Column(Integer, primary_key=True)
    balance = Column(REAL)
    phone = Column(Text)
    tarif = Column(Integer, ForeignKey('tarifs.id'), nullable=False)
    tarif_end = Column(Text)
    status = Column(Text)
    rating = Column(REAL)
    inn = Column(Text)


class Support(Base):
    __tablename__ = 'support'
    username = Column(Text, primary_key=True)
    name = Column(Text)


class Tarif(Base):
    __tablename__ = 'tarifs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    amount = Column(REAL)
    days = Column(Integer)
    publications = Column(Integer)


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    goods = Column(Integer, ForeignKey('goods.id'), nullable=False)
    comment = Column(Text)
    photo_doc = Column(String)
    photo_goods = Column(String)


class BanList(Base):
    __tablename__ = 'ban_list'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text)


from .functions import *
