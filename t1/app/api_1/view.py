# -*- coding: utf-8 -*-
'''
    视图模块
'''
from flask_restful import Resource


class Servers(Resource):
    '''
        多条数据
    '''

    def get(self):
        # 返回所有数据
        return {'message': 'this is data list'}

    def post(self):
        # 新增数据
        return {'message': 'this is post'}


class Server(Resource):
    '''
     单条数据
    '''

    def get(self, _id):
        # 返回单条数据
        return {'message': 'this data is {}'.format(_id)}

    def delete(self, _id):
        # 删除单条数据
        return {'message': 'delete data: {}'.format(_id)}

    def put(self, _id):
        # 修改单条数据
        return {'message': '修改单条数据{}'.format(_id)}
