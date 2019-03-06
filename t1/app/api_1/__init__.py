# -*- coding: utf-8 -*-
'''
    主程序
'''
from flask import Blueprint
assets_page = Blueprint('assets_page', __name__)

from . import main
