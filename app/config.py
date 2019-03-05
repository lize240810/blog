# condig: urf-8
'''
    公共配置文件
    如果有不公开的就创建子类 放入子类之中，调用子类即可
'''


class Config(object):
    SECRET_KEY = 'saduhsuaihfe332r32rfo43rtn3noiYUG9jijoNF23'
    # 七牛云密匙
    QINIU_ACCESS_KEY = "DQ2Vklf0oTr_wLB1OXnrK4A9OqmHTV3DtFY-51rg"
    QINIU_SECRET_KEY  = "uAbAZqS_CQR7weCY1pBtKvzgEEt5odsn3b9622jw"
    # 七牛云存储位置
    BUCKET_NAME = "head_picture"
    # 云通讯的密匙
    YTX_ACCOUNTSID = "8aaf07086904be0b016946b808bf198a"
    YTX_ACCOUNTTOKEN = "de2ae6efd73e4eb9a4eb1433167c4cd2"
    YTX_APPID = "8aaf07086904be0b016946b809151990"
    # templateId，其实就是你添加新的模板的id号，我们这边用开发者账号，直接填写'1'就可以了
    YTX_TEMPLATEID = '1'



    
class DevelopmentConfig(Config):
    '''
        数据库开发配置
    '''
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = '5001'
    # redis 数据库
    REDIS_HOST = "localhost"
    
    REDIS_PORT = 6379
    # 使用的数据库
    REDIS_DB = 4
    # redis数据库密码
    REDIS_PASSWORD = ''
    # MYSQL 数据库配置
    MYSQL_INFO = 'mysql+pymysql://root:root@127.0.0.1:3306/test?charset=utf8'


class ProductionConfig(Config):
    # 成果配置
    DEBUG = False
    # 链接的外部redis
    REDIS_HOST = 'server-ip'
    REDIS_PORT = 6380
    REDIS_DB = 4
    REDIS_PASSWORD = '×××××××××××'
    # 链接的外部mysql
    MYSQL_INFO = "mysql://××××××××××@server-ip:3306/blog01?charset=utf8"

Conf = DevelopmentConfig