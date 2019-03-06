# coding:utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, backref, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

uri = 'mysql+pymysql://root:root@127.0.0.1:3306/test?charset=utf8'

engine = create_engine(uri, echo=True)

Base = declarative_base()
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base.query = db_session.query_property()

from . import user, smallblog
