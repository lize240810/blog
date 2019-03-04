# coding:utf-8
# https://www.cnblogs.com/yueerwanwan0204/p/5330201.html
from flask import Flask, request, jsonify 
from model import User, db_session
import hashlib
import time
import redis

app = Flask(__name__)
redis_store = redis.Redis(host='localhost', port=6379, db=4, password='')


@app.route('/')
def hello_world():
    '''
        测试主页
    '''
    return jsonify({'hello': 'world'}) 


@app.route('/login', methods=['POST'])
def login():
    '''
        用户登录
    '''
    # import ipdb; ipdb.set_trace()
    # 获取用户传入的参数
    phone_number = request.values.get('phone_number')
    password = request.values.get('password')
    
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        return jsonify({'code': 0, 'message': '没有此用户'})

    if user.password != password:
        return jsonify({'code': 0, 'message': '密码错误'})
    # import ipdb; ipdb.set_trace()
    # md5加密
    m = hashlib.md5()
    m.update(phone_number.encode('utf-8'))
    m.update(password.encode('utf-8'))
    m.update( str(int(time.time())).encode('utf-8'))
    token = m.hexdigest()
    # 根据电话号码存入redis数据库
    #  命令用于同时将多个 field-value (字段-值)对设置到哈希表中
    redis_store.hmset('user:{0}'.format(user.phone_number ), {'token': token, 'nickname': user.nickname, 'app_online': 1})
    # 根据md5存入电话
    redis_store.set('token:{0}'.format(token), user.phone_number)
    # Redis Expire 命令用于设置 key 的过期时间，key 过期后将不再可用。单位以秒计
    redis_store.expire('token:{0}'.format(token), 3600*24*30)

    return jsonify({'code': 200, 'message': '成功登录', 'nickname': user.nickname, 'token': token})


@app.route('/user')
def user():
    '''
        查询中带着用户登录的token值
    '''
    token = request.headers.get('token')
    
    if not token:
        return jsonify({'code': 0, 'message': '需要验证'})
    # 传入tokenMD5查询reids数据库查看是否有相同数据
    
    phone_number = redis_store.get('token:{0}'.format(token)).decode('utf-8')
    # redis_store.hget('user:{0}'.format(phone_number), 'token')
    # 查询redis数据库中的哈希表 查询之中是否有存在相关数据 
    
    if not phone_number or token != redis_store.hget('user:{0}'.format(phone_number), 'token').decode('utf-8'):
        # 判断电话号码是否为空 或者判断 md5加密值是否相同
        return jsonify({'code': 2, 'message': '验证信息错误'})
    # 获得昵称
    nickname = redis_store.hget('user:{0}'.format(phone_number), 'nickname').decode('utf-8')
    return jsonify({'code': 200, 'nickname': nickname, 'phone_number': phone_number})


@app.route('/logout')
def logout():
    '''
        用户注销
    '''
    token = request.headers.get('token')
    if not token:
        return jsonify({'code': 0, 'message': '需要验证'})
    phone_number = redis_store.get('token:{0}'.format(token))
    if phone_number :
        phone_number = phone_number.decode('utf-8')
    # import ipdb; ipdb.set_trace()
    if not phone_number or token != redis_store.hget('user:%s' % phone_number, 'token').decode('utf-8'):
        return jsonify({'code': 2, 'message': '验证信息错误'})

    redis_store.delete('token:%s' % token)
    redis_store.hmset('user:%s' % phone_number, {'app_online': 0})
    return jsonify({'code': 200, 'message': '成功注销'})


@app.route('/user/add', methods=['POST'])
def useradd():
    '''
        用户添加
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


@app.route('/user/up', methods=['PUT'])
def userup():
    '''
        用户修改
    '''
    # 得到用户参数
    token = request.headers.get('token')
    new_phone_number = request.values.get('new_phone_number')
    new_password = request.values.get('new_password')
    new_nickname = request.values.get('new_nickname')
    # import ipdb; ipdb.set_trace()
    # 非空判断
    if not token:
        return jsonify({'message': '请先登录', 'code': 0})
    # import ipdb; ipdb.set_trace()
    # 根据登陆的token 获得所登陆者的电话号码
    phone_number = redis_store.get('token:{0}'.format(token))
    if phone_number:
        phone_number.decode('utf-8')
    if not phone_number:
        return jsonify({'message': '请先登录', 'code': 0})
    # 获得用户
    user = User.query.filter_by(phone_number=phone_number).first()
    # 修改电话号码
    if new_phone_number and len(new_phone_number) != 11:
        return jsonify({'message': '电话位数不符合', 'code': 2})

    # 修改密码
    if new_password and len(new_password) < 6 :
        return jsonify({'message': '密码至少六位数', 'code': 2})
    # import ipdb; ipdb.set_trace()
    # 判断输入的密码和电话是否有为空的 不为空则修改原始数据
    if new_phone_number:
        user.phone_number = phone_number
    if new_password:
        user.password = new_password
    # 判断用户昵称是否修改了
    if new_nickname:
        user.nickname = new_nickname

    db_session.add(user)
    db_session.flush()
    db_session.commit()
    redis_store.delete('token:%s' % token)
    redis_store.delete('user:%s' % phone_number)
    return jsonify({'message': '修改成功，请重新登陆', 'code': 200})

@app.teardown_request
def handle_teardown_request(exception):
    '''最后一个很重要，这边一定要记住，把这个函数写上。如果没有这个函数，每一个会话以后，
    db_session都不会清除，很多时候，数据库改变了，前台找不到，或者明明已经提交，
    数据库还是没有更改，或者长时间没有访问接口，mysql gong away，这样的错误。总之，一定要加上。'''
    db_session.remove()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)