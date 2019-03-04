# coding:utf-8
import requests
import json
from qiniu import put_file


class APITest(object):
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {}
        self.token = None
        self.qiniu_token = None
        self.qiniu_key = None
        self.qiniu_base_url = 'http://pntn3xhqe.bkt.clouddn.com/'

    def login(self, phone_number, password, path='/login'):
        payload = {'phone_number': phone_number, 'password': password}
        self.headers = {'content-type': 'application/json'}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        self.token = response_data.get('token')
        return response_data

    def user(self, path='/user'):
        self.headers = {'token': self.token}
        response = requests.get(url=self.base_url + path, headers=self.headers)
        response_data = json.loads(response.content)
        return response_data

    def logout(self, path='/logout'):
        self.headers = {'token': self.token}
        response = requests.get(url=self.base_url + path, headers=self.headers)
        response_data = json.loads(response.content)
        return response_data

    def get_qiniu_token(self, path='/get-qiniu-token'):
        response = requests.get(url=self.base_url + path)
        response_data = json.loads(response.content)
        self.qiniu_token = response_data.get('token')
        self.qiniu_key = response_data.get('key')
        if self.qiniu_token and self.qiniu_key:
            print '成功获取qiniu_token和qiniu_key,分别为%s和%s' % (self.qiniu_token.encode('utf-8'), self.qiniu_key.encode('utf-8'))
            localfile = '/home/yudahai/PycharmProjects/blog01/app/my-test.png'
            ret, info = put_file(self.qiniu_token, self.qiniu_key, localfile)
            print info.status_code
            if info.status_code == 200:
                print '上传成功'
                self.head_picture = self.qiniu_base_url + self.qiniu_key
                print '其url为:' + self.head_picture.encode('utf-8')
            else:
                print '上传失败'
        return response_data

    def set_head_picture(self, path='/set-head-picture'):
        payload = {'head_picture': self.head_picture}
        self.headers = {'token': self.token, 'content-type': 'application/json'}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        print response_data.get('message')
        return response_data

if __name__ == '__main__':
    api = APITest('http://127.0.0.1:5001')
    api.login('13565208554', '123456')
    api.get_qiniu_token()
    api.set_head_picture()
    api.logout()