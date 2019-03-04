# coding:utf-8
'''
    启动文件 入口
'''
from flask import Flask
from config import Conf
import redis
from qiniu import Auth, put_file, etag, urlsafe_base64_encode


def create_app():
    app = Flask(__name__)
    app.config.from_object(Conf)
    # app密匙
    app.secret_key = app.config['SECRET_KEY']
    # redis配置
    app.redis = redis.Redis(
        host=app.config['REDIS_HOST'], 
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB'],
        password=app.config['REDIS_PASSWORD']
    )
    # 七牛云配置
    app.q = Auth(access_key = app.config['QINIU_ACCESS_KEY'],
            secret_key = app.config['QINIU_SECRET_KEY']
        )
    # 七牛云文件存储位置
    app.bucket_name = app.config['BUCKET_NAME']
    # 启动配置
    app.debug = app.config['DEBUG']        
    app.host=app.config['HOST']
    app.port=app.config['PORT']

    # 树根指向树枝的代码
    from app.app_1_0 import api as api_1_0_blueprint
    # 注册蓝图
    # 路径前缀
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1000')

    # 树根指向树枝的代码
    from app.app_1_1 import api as api_1_1_blueprint
    # 注册蓝图
    # 路径前缀
    app.register_blueprint(api_1_1_blueprint, url_prefix='/api/v1100')
    
    return app


if __name__ == '__main__':
    app = create_app()
    # import ipdb; ipdb.set_trace()
    app.run(debug=app.debug, host=app.host, port=app.port)