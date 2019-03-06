import datetime

from sqlalchemy import (
	ForeignKey,
	Column,
	Integer,
	String,
	Text,
	DateTime
)
from sqlalchemy.orm import relationship, backref
from . import Base
from .top1 import User


class SmallBlog(Base):
    '''
        小型博客
    '''
    __tablename__ = 'small_blog'

    id = Column('id', Integer, primary_key=True)
    # 外键
    post_user_id = Column('post_user_id', Integer, ForeignKey(User.id))
    # 发布时间 默认值
    post_time = Column('post_time', DateTime, default=datetime.datetime.now)
    title = Column('title', String(30), index=True)
    text_content = Column('text_content', Text)
    picure_content = Column(String(900))
    # 关系
    post_user = relationship('User', backref=backref('small_blogs'))
