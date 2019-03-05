# coding:utf-8
'''
    1. 优化代码添加装饰器
    2. 设置请求发送之前触发的函数
    3. 改变redis的通道
    4. 使用了配置文件
    5. 运行的代码取消了，统一了入口点
    6. app.router 改成 api.route api 从本地__init__.py中导入
    7. app.redis，可以用current_app.redis来代替，其实就是在run.py中定义的一些变量，在整颗树中使用。
'''
import hashlib
import time
import uuid
import sys
import redis


import redis
from functools import wraps # 装饰器
from qiniu import Auth, put_file, etag, urlsafe_base64_encode # 七牛云
from flask import Flask, request, jsonify, g, render_template, redirect, url_for, session, current_app

from . import api
from app.model import db_session, User

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


@api.route('/login', methods=['POST'])
def login():
    '''
        用户登录
    '''
    # 获取用户传入的参数
    phone_number = request.values.get('phone_number')
    password = request.values.get('password')
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        return jsonify({'code': 0, 'message': '没有此用户'})

    if user.password != password:
        return jsonify({'code': 0, 'message': '密码错误'})
    # 查询是否登录
    if current_app.redis.hget('user:{0}'.format(phone_number), 'token'):
        return jsonify({'message': '您已登录，不需再次登录', 'code':'0'})

    # md5加密
    m = hashlib.md5()
    m.update(phone_number.encode('utf-8'))
    m.update(password.encode('utf-8'))
    m.update( str(int(time.time())).encode('utf-8'))
    token = m.hexdigest()
    # 根据电话号码存入redis数据库
    #  命令用于同时将多个 field-value (字段-值)对设置到哈希表中
    # 创建redis通道
    pipeline = current_app.redis.pipeline()
    pipeline.hmset('user:{0}'.format(user.phone_number ), {'token': token, 'nickname': user.nickname, 'app_online': 1})
    # 根据md5存入电话
    pipeline.set('token:{0}'.format(token), user.phone_number)
    # Redis Expire 命令用于设置 key 的过期时间，key 过期后将不再可用。单位以秒计
    pipeline.expire('token:{0}'.format(token), 3600*24*30)
    # 关闭通道
    pipeline.execute()
    return jsonify({'code': 200, 'message': '成功登录', 'nickname': user.nickname, 'token': token})


@api.route('/user')
@login_check
def user():
    '''
        查询用户
    '''
    user = g.current_user
    # 获得昵称
    nickname = current_app.redis.hget('user:{0}'.format(user.phone_number), 'nickname').decode('utf-8')
    return jsonify({'code': 200, 'nickname': nickname, 'phone_number': user.phone_number})


@api.route('/logout')
@login_check
def logout():
    '''
        用户注销
    '''
    user = g.current_user
    # 修改redis 的通道
    pipeline = current_app.redis.pipeline()
    # 删除reids中的token
    pipeline.delete('token:{0}'.format(g.token))
    # 存入hash的数据
    pipeline.hmset('user:{0}'.format(user.phone_number), {'app_online': 0})
    pipeline.execute()
    return jsonify({'code': 200, 'message': '成功注销'})


@api.route('/user/register', methods=['POST'])
def userregister():
    '''
        用户注册
    '''
    # 得到用户参数
    phone_number = request.values.get('phone_number')
    password = request.values.get('password')
    nickname = request.values.get('nickname')
    # 非空判断
    if not phone_number:
        return jsonify({'message': '请输入电话号码', 'code': 0})
    elif len(phone_number) != 11:
        return jsonify({'message': '电话位数不符合', 'code': 2})

    if not password:
        return jsonify({'message': '密码不允许为空', 'code': 0})
    if len(password) < 6:
        return jsonify({'message': '密码至少六位数', 'code': 2})
    
    if not nickname:
        nickname = 'zhangsan'
    
    # 判断号码是否被使用
    user = User.query.filter_by(phone_number=phone_number).first()
    # import ipdb; ipdb.set_trace()
    if user:
        return jsonify({'message': '该号码已被注册', 'code': 1})
    u1 = User()
    u1.password= password
    u1.phone_number= phone_number
    u1.nickname = nickname
    # import ipdb; ipdb.set_trace()
    db_session.add(u1)
    db_session.flush()
    db_session.commit()
    # import ipdb; ipdb.set_trace()    
    return jsonify({'message': '注册成功', 'code': 200})


@api.route('/user/alter', methods=['PUT'])
@login_check
def useralter():
    '''
        用户修改
    '''
    # 得到用户参数
    new_phone_number = request.values.get('new_phone_number')
    new_password = request.values.get('new_password')
    new_nickname = request.values.get('new_nickname')
    # 根据登陆的token 获得所登陆者的电话号码
    
    # 获得用户
    user = g.current_user
    # 修改电话号码
    if new_phone_number and len(new_phone_number) != 11:
        return jsonify({'message': '电话位数不符合', 'code': 2})

    # 修改密码
    if new_password and len(new_password) < 6 :
        return jsonify({'message': '密码至少六位数', 'code': 2})
    # import ipdb; ipdb.set_trace()
    # 判断输入的密码和电话是否有为空的 不为空则修改原始数据
    # 原始电话
    phone_number = user.phone_number

    if new_phone_number:
        user.phone_number = new_phone_number
    if new_password:
        user.password = new_password
    # 判断用户昵称是否修改了
    if new_nickname:
        user.nickname = new_nickname

    db_session.add(user)
    db_session.flush()
    db_session.commit()

    
    current_app.redis.delete('token:{0}'.format(g.token))
    current_app.redis.delete('user:{0}'.format(phone_number))

    return jsonify({'message': '修改成功，请重新登陆', 'code': 200})


@api.route('/get-qiniu-token')
def get_qiniu_token(phone_number):
    '''
        获得七牛云的token和key
    '''
    key = '{0}/{1}.jpg'.format(phone_number, time.time_ns())
    # uuid.uuid4()
    token = current_app.q.upload_token(current_app.bucket_name, key, 3600)
    return jsonify({'code': 1, 'key': key, 'token': token})


@api.route('/set-head-picture', methods=['POST'])
@login_check
def set_head_picture():
    '''
        图片名存储到数据库
    '''
    user = g.current_user
    # 获得图片的七牛云图片
    # import ipdb; ipdb.set_trace()
    head_picture = get_qiniu_token(user.phone_number).json
    code, key, token = get_qiniu_token(user.phone_number).json.values()
    # 用户提交的图片
    up_head_picture = request.values.get('head_picture')
    head_picture = 'http://pntn3xhqe.bkt.clouddn.com/{0}'.format(key)
    user.head_picture = head_picture
    # 图片上传
    localfile = r'{0}'.format(up_head_picture)
    ret, info = put_file(token, key, localfile)
    try:
        db_session.commit()
    except Exception as e:
        print(e)
        db_session.rollback()
        return jsonify({'code': 0, 'message': '未能成功上传'})
    current_app.redis.hset('user:{0}'.format(user.phone_number), 'head_picture', head_picture)
    return jsonify({'code': 1, 'message': '成功上传'})

@api.teardown_request
def handle_teardown_request(exception):
    '''最后一个很重要，这边一定要记住，把这个函数写上。如果没有这个函数，每一个会话以后，
    db_session都不会清除，很多时候，数据库改变了，前台找不到，或者明明已经提交，
    数据库还是没有更改，或者长时间没有访问接口，mysql gong away，这样的错误。总之，一定要加上。'''
    db_session.remove()
