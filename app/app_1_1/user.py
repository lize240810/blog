# coding: utf-8
'''
    用户模块类
    登录， 查询，注销
    注册，修改
'''
import hashlib
import time
import random

from flask import (
    Flask, request, jsonify, g, current_app
)

from app.model import User, db_session
from .decorators import login_check
from . import api
from app.utils import message_validate


@api.route('/login', methods=['POST'])
def login():
    '''
        用户登录
    '''
    # 获取用户传入的参数
    phone_number = request.values.get('phone_number')
    # 加密密码
    password = request.values.get('password')
    
    user = User.query.filter_by(phone_number=phone_number).first()

    # encryption_str就是加密串用sha256加密的
    s= hashlib.sha256()
    s.update(password.encode('utf-8'))
    s.update(phone_number[:3:2].encode('utf-8'))
    s.update('password'.encode('utf-8'))
    encryption_str = s.hexdigest()

    if not user:
        return jsonify({'code': 0, 'message': '没有此用户'})

    if user.password != encryption_str:
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


@api.route('/user/register-step-1', methods=['POST'])
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

        # 判断号码是否被使用
    user = User.query.filter_by(phone_number=phone_number).first()
    if user:
        return jsonify({'message': '该号码已被注册', 'code': 1})

    if not password:
        return jsonify({'message': '密码不允许为空', 'code': 0})
    if len(password) < 6:
        return jsonify({'message': '密码至少六位数', 'code': 2})
    
    if not nickname:
        nickname = 'zhangsan'
    
    s= hashlib.sha256()
    s.update(password.encode('utf-8'))
    s.update(phone_number[:3:2].encode('utf-8'))
    s.update('password'.encode('utf-8'))
    encryption_str = s.hexdigest()
    

    u1 = User()
    u1.password= encryption_str
    u1.phone_number= phone_number
    u1.nickname = nickname
    db_session.add(u1)
    db_session.flush()
    db_session.commit()
    return jsonify({'message': '注册成功', 'code': 200})


@api.route('/send_sms', methods=['POST'])
def send_validate_number():
    """
        接受phone_number,发送短信
    """
    phone_number = request.values.get('phone_number')
    # 获得验证码
    validate_number = str(random.randint(100000, 1000000))
    # 判断号码是否被使用
    user = User.query.filter_by(phone_number = phone_number).first()
    if user:
        return jsonify({'code': 0, 'message': '该用户已经存在,注册失败'})

    # 用户的电话和验证码
    result, err_message = message_validate(phone_number, validate_number)
    # 发送失败
    if not result:
        return jsonify({'code': 0, 'message': err_message})
    pipeline = current_app.redis.pipeline()
    pipeline.set('validate:%s' % phone_number, validate_number)
    # 设置存在时间为60秒
    pipeline.expire('validate:%s' % phone_number, 600)
    pipeline.execute()
    return jsonify({'code': 200, 'message': '发送成功'})


@api.route('/verification_validate_number', methods=['POST'])
def verification_validate_number():
    '''
        验证码验证
    '''
    phone_number = request.values.get('phone_number')

    # 获取验证码
    validate_number = request.values.get('validate_number')
    
    # redis中的验证码
    validate_number_redis = current_app.redis.get('validate:{0}'.format(phone_number))
    if validate_number_redis:
        validate_number_redis = validate_number_redis.decode('utf-8')
    
    if validate_number != validate_number_redis:
        return jsonify({'code': 2, 'message': '验证码不正确'})
    
    # 创建新的通道
    pipe_line = current_app.redis.pipeline()
    # 验证码验证成功以后根据号码存入1 
    pipe_line.set('is_validate:%s' % phone_number, '1')
    # 两分钟过期
    pipe_line.expire('is_validate:%s' % phone_number, 120)
    # 销毁redis通道
    pipe_line.execute()
 
    return jsonify({'code': 1, 'message': '短信验证通过'})


@api.route('/password_verify', methods=['POST'])
def password_verify():
    '''
        密码验证
    '''
    phone_number = request.values.get('phone_number')
    password = request.values.get('password')
    password_confirm = request.values.get('password_confirm')
    
    if not password:
        return jsonify({'message': '密码不允许为空', 'code': 0})
    if len(password) < 6:
        return jsonify({'message': '密码至少六位数', 'code': 2})
    if password_confirm != password :
        return jsonify({'message': '两次输入的密码不相同', 'code': 2})
    # 获取redis中数据
    is_validate = current_app.redis.get('is_validate:{0}'.format(phone_number))
    if is_validate:
        if is_validate.decode('utf-8') != '1' :
            return jsonify({'message':'验证码不正确', 'code':'2'})
    
    # 密码加密
    s = hashlib.sha256()
    s.update(password.encode('utf-8'))
    s.update(phone_number[:3:2].encode('utf-8'))
    s.update('password'.encode('utf-8'))
    encryption_str = s.hexdigest()
    # 创建redis通道
    pipeline = current_app.redis.pipeline() 
    pipeline.hset('register:{0}'.format(phone_number), 'password',encryption_str)
    pipeline.expire('register:%s' % phone_number, 200)
    pipeline.execute()
    return jsonify({'code':200, 'message':' 提交密码成功'})


@api.route('/user/register-step-2', methods=['POST'])
def userregister_2():
    '''
        用户注册
    '''
    phone_number = request.values.get('phone_number')
    nickname = request.values.get('nickname')
    # 非空判断
    if not phone_number:
        return jsonify({'message': '请输入电话号码', 'code': 0})
    elif len(phone_number) != 11:
        return jsonify({'message': '电话位数不符合', 'code': 2})
    import ipdb; ipdb.set_trace()
    # 从redis中获取验证码是否验证成功
    is_validate = current_app.redis.get('is_validate:{0}'.format(phone_number))
    if is_validate:
        is_validate = is_validate.decode('utf-8')
    if is_validate != '1':
        return jsonify({'code':0, 'message': '验证码没验证成功'})

    # 获取password 
    password = current_app.redis.hget('register:{0}'.format(phone_number),'password')
    if password:
        password = password.decode('utf-8')
    if not nickname:
        nickname = '张三同学'
    new_user = User(phone_number=phone_number, password=password, nickname=nickname)    
    db_session.add(new_user)

    try:
        db_session.commit()
    except Exception as e:
        print(e)
        db_session.rollback()
        return jsonify({'code':1, 'message': '注册失败'})
    finally:
        current_app.redis.delete('is_validate:{0}'.format(phone_number))
        current_app.redis.delete('register:{0}'.format(phone_number))
    
    return jsonify({'code': 200, 'message': '注册成功'})


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