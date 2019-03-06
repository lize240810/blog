import datetime

from sqlalchemy import ForeignKey, Column, Integer, String, Text, DateTime
from . import Base


class User(Base):
    '''
        用户类
    '''
    __tablename__ = 'user'

    id = Column('id', Integer, primary_key=True)
    phone_number = Column('phone_number', String(11), index=True)
    password = Column('password', String(100))
    nickname = Column('nickname', String(250), index=True, nullable=True)
    head_picture = Column('head_picture', String(200), default='')
    register_time = Column('register_time', DateTime, index=True, default = datetime.datetime.now)
