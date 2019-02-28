# coding:utf-8
# https://www.cnblogs.com/yueerwanwan0204/p/5330201.html
import datetime

from flask import Flask, request, jsonify 
from model import User, db_session
import hashlib
import time
import redis

app = Flask(__name__)
redis_store = redis.Redis(host='localhost', port=6379, db=4, password='')


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/login', methods=['POST'])
def login():
    # import ipdb; ipdb.set_trace()
    # 获取用户传入的参数
    phone_number = request.values.get('phone_number')
    password = request.values.get('password')
    
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        return jsonify({'code': 0, 'message': '没有此用户'})

    if user.password != password:
        return jsonify({'code': 0, 'message': '密码错误'})
    import ipdb; ipdb.set_trace()
    m = hashlib.md5()
    m.update(phone_number.encode('utf-8'))
    m.update(password.encode('utf-8'))
    m.update( str(int(time.time())).encode('utf-8'))
    token = m.hexdigest()

    redis_store.hmset('user:%s' % user.phone_number, {'token': token, 'nickname': user.nickname, 'app_online': 1})
    redis_store.set('token:%s' % token, user.phone_number)
    redis_store.expire('token:%s' % token, 3600*24*30)

    return jsonify({'code': 1, 'message': '成功登录', 'nickname': user.nickname, 'token': token})


@app.route('/user')
def user():
    token = request.headers.get('token')
    if not token:
        return jsonify({'code': 0, 'message': '需要验证'})
    phone_number = redis_store.get('token:%s' % token)
    if not phone_number or token != redis_store.hget('user:%s' % phone_number, 'token'):
        return jsonify({'code': 2, 'message': '验证信息错误'})

    nickname = redis_store.hget('user:%s' % phone_number, 'nickname')
    return jsonify({'code': 1, 'nickname': nickname, 'phone_number': phone_number})


@app.route('/logout')
def logout():
    token = request.headers.get('token')
    if not token:
        return jsonify({'code': 0, 'message': '需要验证'})
    phone_number = redis_store.get('token:%s' % token)
    if not phone_number or token != redis_store.hget('user:%s' % phone_number, 'token'):
        return jsonify({'code': 2, 'message': '验证信息错误'})

    redis_store.delete('token:%s' % token)
    redis_store.hmset('user:%s' % phone_number, {'app_online': 0})
    return jsonify({'code': 1, 'message': '成功注销'})

@app.route('/user/add', methods=['POST'])
def useradd():
    # 得到用户参数
    phone_number = request.values.get('phone_number')
    password = request.values.get('password')
    nickname = request.values.get('nickname')
    # 非空判断
    if not phone_number:
        return jsonify({'message': '请输入电话号码', 'code': 0})
    elif len(phone_number) != 11:
        return jsonify({'message': '电话位数不符合', 'code': 1})

    if not password:
        return jsonify({'message': '密码不允许为空', 'code': 0})
    elif not len(password) <= 6:
        return jsonify({'message': '密码至少六位数', 'code': 1})
    
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
    u1.nickname = nickname.encode('utf-8')
    db_session.add(u1)
    db_session.flush()
    db_session.commit()
    
    return jsonify({})

@app.teardown_request
def handle_teardown_request(exception):
    db_session.remove()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)