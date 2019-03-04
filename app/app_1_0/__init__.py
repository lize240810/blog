# config: utf-8
'''
    存放1.0版本的
    使用蓝图
'''
from flask import Blueprint
# 定义一个蓝图 蓝图名就叫api
api = Blueprint('api', __name__)

'''
    在这边，你导入一次，就是就是告诉上级，这边还有个view.py文件，
    里面覆盖了一些接口。
    整个根就知道，哦，如果有接口访问这，我就指向你这边
'''
from . import view_2


