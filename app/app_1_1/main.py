# coding:utf-8
'''
    app_1_1 主程序
    获取七牛云token 
    图片上传
    图片保存
    数据库关闭
'''
'''
    1. 优化代码添加装饰器
    2. 设置请求发送之前触发的函数
    3. 改变redis的通道
    4. 使用了配置文件
    5. 运行的代码取消了，统一了入口点
    6. app.router 改成 api.route api 从本地__init__.py中导入
    7. app.redis，可以用current_app.redis来代替，其实就是在run.py中定义的一些变量，在整颗树中使用。
'''

import time
import uuid
import random
import redis


from qiniu import Auth, put_file, etag, urlsafe_base64_encode # 七牛云
from flask import Flask, request, jsonify, g, render_template, redirect, url_for, session, current_app


from app.model import db_session, User, SmallBlog
from . import api
from .decorators import login_check


# 在放请求之前使用的方法
@api.before_request
def before_request():
    token = request.headers.get('token')
    # 获得电话号码        
    phone_number = current_app.redis.get('token:{0}'.format(token))
    # 查询数据库并返回设置为全局参数
    if phone_number:
        phone_number = phone_number.decode('utf-8')
        g.current_user = User.query.filter_by(phone_number=phone_number).first()
        g.token = token
    return 


@api.teardown_request
def handle_teardown_request(exception):
    '''最后一个很重要，这边一定要记住，把这个函数写上。如果没有这个函数，每一个会话以后，
    db_session都不会清除，很多时候，数据库改变了，前台找不到，或者明明已经提交，
    数据库还是没有更改，或者长时间没有访问接口，mysql gong away，这样的错误。总之，一定要加上。'''
    db_session.remove()


@api.route('/get-qiniu-token')
def get_qiniu_token(phone_number):
    '''
        获得七牛云的token和key
    '''
    key = '{0}/{1}.jpg'.format(phone_number, time.time_ns())
    # uuid.uuid4()
    token = current_app.q.upload_token(current_app.bucket_name, key, 3600)
    return jsonify({'code': 1, 'key': key, 'token': token})


@api.route('/get-multi-qiniu-token')
@login_check
def get_multi_qiniu_token():
    '''
        获取多个七牛token
    '''
    count = request.args.get('count')

    if not 0 < int(count) < 10:
        return jsonify({'code': 0, 'message': '一次只能获取1到9个'})

    key_token_s = []
    for x in range(int(count)):
        key = uuid.uuid1()
        token = current_app.q.upload_token(current_app.bucket_name, key, 3600)
        key_token_s.append((key, token))
    return jsonify({'code': 1, 'key_token_s': key_token_s})
