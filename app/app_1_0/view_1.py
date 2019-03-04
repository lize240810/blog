# coding:utf-8
'''
    1. 优化代码添加装饰器
    2. 设置请求发送之前触发的函数
    3. 改变redis的通道
'''
import hashlib
import time
import uuid

from flask import Flask, request, jsonify, g
import redis
from qiniu import Auth, put_file, etag, urlsafe_base64_encode # 七牛云
from functools import wraps # 装饰器

from model import User, db_session

# 七牛云密匙
access_key = "DQ2Vklf0oTr_wLB1OXnrK4A9OqmHTV3DtFY-51rg"
secret_key = "uAbAZqS_CQR7weCY1pBtKvzgEEt5odsn3b9622jw"

# 实例化七牛云的权限对象
q = Auth(access_key=access_key, secret_key=secret_key)
# 七牛云存储的内容
bucket_name = 'head_picture'

app = Flask(__name__)
redis_store = redis.Redis(host='localhost', port=6379, db=4, password='')

# 装饰器函数
def login_check(f):
    '''
        优化代码 方法进行token验证的时候优化一次
    '''
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('token')
        if not token:
            return jsonify({'code': 0, 'message': '请先登录'})
        
        phone_number = redis_store.get('token:{0}'.format(token))
        if phone_number:
            phone_number = phone_number.decode('utf-8')
        # import ipdb; ipdb.set_trace()
        if not phone_number or token != redis_store.hget('user:%s' % phone_number, 'token').decode('utf-8'):
            return jsonify({'code': 2, 'message': '验证信息错误'})

        return f(*args, **kwargs)
    return decorator

# 在放请求之前使用的方法
@app.before_request
def before_request():
    token = request.headers.get('token')
    # 获得电话号码        
    phone_number = redis_store.get('token:{0}'.format(token))
    # 查询数据库并返回设置为全局参数
    if phone_number:
        # import ipdb; ipdb.set_trace()
        phone_number = phone_number.decode('utf-8')
        g.current_user = User.query.filter_by(phone_number=phone_number).first()
        g.token = token


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
    # import ipdb; ipdb.set_trace()
    user = User.query.filter_by(phone_number=phone_number).first()
    
    if not user:
        return jsonify({'code': 0, 'message': '没有此用户'})

    if user.password != password:
        return jsonify({'code': 0, 'message': '密码错误'})
    # 查询是否登录
    if redis_store.hget('user:{0}'.format(phone_number), 'token'):
        return jsonify({'message': '您已登录，不需再次登录', 'code':'0'})

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
@login_check
def user():
    '''
        查询用户
    '''
    import ipdb; ipdb.set_trace()
    user = g.current_user
    # 获得昵称
    nickname = redis_store.hget('user:{0}'.format(user.phone_number), 'nickname').decode('utf-8')
    return jsonify({'code': 200, 'nickname': nickname, 'phone_number': user.phone_number})


@app.route('/logout')
@login_check
def logout():
    '''
        用户注销
    '''
    user = g.current_user
    # 修改redis 的通道
    pipeline = redis_store.pipeline()
    pipeline.delete('token:%s' % g.token)
    # 存入hash的数据
    pipeline.hmset('user:{0}'.format(user.phone_number), {'app_online': 0})
    pipeline.execute()
    return jsonify({'code': 200, 'message': '成功注销'})


@app.route('/user/register', methods=['POST'])
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


@app.route('/user/alter', methods=['PUT'])
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

    
    redis_store.delete('token:{0}'.format(g.token))
    redis_store.delete('user:{0}'.format(phone_number))

    return jsonify({'message': '修改成功，请重新登陆', 'code': 200})


@app.route('/get-qiniu-token')
def get_qiniu_token(phone_number):
    '''
        获得七牛云的token和key
    '''
    key = '{0}/{1}.jpg'.format(phone_number, time.time_ns())
    # uuid.uuid4()
    token = q.upload_token(bucket_name, key, 3600)
    # import json
    # json.dump()
    return jsonify({'code': 1, 'key': key, 'token': token})


@app.route('/set-head-picture', methods=['POST'])
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
    redis_store.hset('user:{0}'.format(user.phone_number), 'head_picture', head_picture)
    return jsonify({'code': 1, 'message': '成功上传'})

@app.teardown_request
def handle_teardown_request(exception):
    '''最后一个很重要，这边一定要记住，把这个函数写上。如果没有这个函数，每一个会话以后，
    db_session都不会清除，很多时候，数据库改变了，前台找不到，或者明明已经提交，
    数据库还是没有更改，或者长时间没有访问接口，mysql gong away，这样的错误。总之，一定要加上。'''
    db_session.remove()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)