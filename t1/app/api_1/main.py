# -*- coding: utf-8 -*-
'''
主程序
'''

from flask_restful import Api

from . import assets_page
from .view import Servers, Server
api = Api(assets_page)

# 注册路由
api.add_resource(Servers, '/servers')
api.add_resource(Server, '/servers/<_id>')
