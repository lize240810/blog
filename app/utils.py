import random
# coding:utf-8
'''
    工具类
	云通讯短信验证：https://www.yuntongxun.com/member/smsTemplate/toAdd
    
'''
import datetime
import hashlib
import requests
import json
import base64

from .config import Conf


def message_validate(phone_number, validate_number):
    '''
        云通讯验证码
    '''
    if not phone_number:
        return {'message': '请输入电话号码', 'code': 0}
    elif len(phone_number) != 11:
        return {'message': '电话位数不符合', 'code': 2}
    
    # 获取当前时间
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    # 获得一组数据 拼接字符串
    signature = Conf.YTX_ACCOUNTSID + Conf.YTX_ACCOUNTTOKEN + now
    m = hashlib.md5()
    m.update(signature.encode('utf-8'))
    # 获得加密后·的密文全部转换为大写
    sigParameter = m.hexdigest().upper()
    # sigParameter = hashlib.md5().update(signature).hexdigest().upper()
    # 发送请求
    url = "https://sandboxapp.cloopen.com:8883/2013-12-26/Accounts/{0}/SMS/TemplateSMS?sig={1}".format(Conf.YTX_ACCOUNTSID, sigParameter)
    # 授权id 加时间
    authorization = Conf.YTX_ACCOUNTSID + ':' + now
    # 转换为base64码
    new_authorization = base64.encodestring(authorization.encode('utf-8')).strip()
	# 请求头    
    headers = {'content-type': 'application/json;charset=utf-8', 'accept': 'application/json',
               'Authorization': new_authorization}
    # 请求所带的数据
    data = {
    	# 需要发送的电话号码
    	'to': phone_number, 
    	'appId': Conf.YTX_APPID, 
    	# 模板Id
    	'templateId': Conf.YTX_TEMPLATEID, 
    	# 验证码
    	'datas': [str(validate_number), '3']
    }

    response = requests.post(url=url, data=json.dumps(data), headers=headers)
    if response.json()['statusCode'] == '000000':
        return True, response.json().get('templateSMS')
    else:
        return False, response.json().get('statusMsg')


if __name__ == '__main__':
    result, reason = message_validate('13251341944', '123456')
    if result:
        print( '发送成功')
    else:
        print( '发送失败')
        print( '原因是:' + reason.encode('utf-8'))