import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(250), nullable=False, unique=True)
    name = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'email': self.email,
            'name': self.name,
            'id': self.id,
        }


class Categories(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class CategoryItem(Base):
    __tablename__ = 'category_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_name = Column(String(250), ForeignKey('category.name'))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship("Categories", foreign_keys=[category_id],
                            backref=backref("item",
                            cascade="all, delete-orphan"))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'category': self.category_name,
        }


# class Userpic(Base):
#     __tablename__ = 'userpic'

#     id = Column(Integer, primary_key=True)
#     picaddress = Column(String(250), nullable=False, unique=True)
#     picname = Column(String(250))

#     @property
#     def serialize(self):
#         """Return object data in easily serializeable format"""
#         return {
#             'picaddress': self.picaddress,
#             'picname': self.picname,
#             'id': self.id,
#         }


engine = create_engine('sqlite:////var/www/FlaskApps/catalog/dbfile/catalog.db')


Base.metadata.create_all(engine)
