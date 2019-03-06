# -*- coding: utf-8 -*-

from flask import Flask
from models import *


# 导入蓝图实例
from app.api_1 import assets_page

app = Flask(__name__)

# 注册蓝图
app.register_blueprint(assets_page)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(host='0.0.0.0', port=5000, debug=True)
# https://blog.csdn.net/hn8081com/article/details/82593202