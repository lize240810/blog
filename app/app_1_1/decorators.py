# coding: utf-8
'''
    装饰器
    用户验证，
    用户登录后获取电话号码
'''
from functools import wraps # 装饰器
from flask import (
    Flask, request, jsonify, g, current_app
)
from app.model import User
from . import api

def login_check(f):
    '''
        装饰器函数
        优化代码 方法进行token验证的时候优化一次
    '''
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('token')
        if not token:
            return jsonify({'code': 0, 'message': '请先登录'})
        # 从redis中获取电话号码
        phone_number = current_app.redis.get('token:{0}'.format(token))
        if phone_number:
            phone_number = phone_number.decode('utf-8')
        # 验证
        if not phone_number or token != current_app.redis.hget('user:{0}'.format(phone_number), 'token').decode('utf-8'):
            return jsonify({'code': 2, 'message': '验证信息错误'})

        return f(*args, **kwargs)
    return decorator


