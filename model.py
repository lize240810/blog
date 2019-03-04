# coding:utf-8
import datetime

from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Text, DateTime,\
    and_, or_, SmallInteger, Float, DECIMAL, desc, asc, Table, join, event
from sqlalchemy.orm import relationship, backref, sessionmaker, scoped_session, aliased, mapper
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm.collections import attribute_mapped_collection
from config import Conf

# import ipdb; ipdb.set_trace()
# uri = 'mysql+pymysql://root:root@127.0.0.1:3306/test?charset=utf8'
engine = create_engine(
    Conf.MYSQL_INFO,
    echo=True)

Base = declarative_base()

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base.query = db_session.query_property()


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
    register_time = Column('register_time', DateTime, index=True, default=datetime.datetime.now)


class SmallBlog(Base):
    '''
        小型博客
    '''
    __tablename__ = 'small_blog' 

    id = Column('id', Integer, primary_key=True)
    # 外键
    post_user_id = Column('post_user_id', Integer, ForeignKey(User.id))
    # 发布时间 默认值
    post_time = Column('post_time', DateTime, default = datetime.datetime.now)
    title = Column('title', String(30), index=True)
    text_content = Column('text_content', Text)
    picure_content = Column(String(900))
    # 关系
    post_user = relationship('User', backref=backref('small_blogs'))
    

    @hybrid_property
    def pictures(self):
        '''
            把方法添加为类属性
        '''
        import ipdb; ipdb.set_trace()
        if not self.picture_content:
            return []
        return self.picture_content.split(',')


    @pictures.setter
    def pictures(self, urls):
        import ipdb; ipdb.set_trace()
        self.picture_content = urls

    def to_dict(self):
        '''
            为返回json格式数据做准备
        '''
        return {
            'id': self.id,
            'post_user_picture': self.post_user.head_picture,
            'post_user_name': self.post_user.nickname,
            'post_time': self.post_time.strftime('%Y-%m-%d %H:%M:%S'),
            'title': self.title,
            'text_content': self.text_content,
            'pictures': self.pictures
        }


if __name__ == '__main__':
    Base.metadata.create_all(engine)