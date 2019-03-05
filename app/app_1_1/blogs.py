# coding: utf-8
'''
    博文视图
'''
from flask import (
    Flask, request, jsonify, g, current_app
)
from sqlalchemy import and_, or_, desc, asc, join, event

from app.model import db_session, User, SmallBlog
from . import api
from .decorators import login_check

@api.route('/post-blog', methods=['POST'])
@login_check
def post_blog():
    '''
        提交新的博文
    '''
    user = g.current_user
    # 接受参数
    title = request.values.get('title')
    text_content = request.values.get('text_content')
    pictures = request.values.get('pictures')
    # 实例化一个新的博文
    newblog = SmallBlog(title=title, text_content=text_content, post_user=user)
    # 博文图片
    newblog.pictures = pictures
    db_session.add(newblog)
    try:
        db_session.commit()
    except Exception as e:
        print(e)
        db_session.rollback()
        return jsonify({'code': 0, 'message': '上传不成功'})
    return jsonify({'code': 1, 'message': '上传成功'})


@api.route('/get-blogs')
@login_check
def get_blogs():
    '''
        查询前10条
        last_id 等于0 或者不填 查询全部数据的前10条
        last_id 等于10 查询id小于10的数据的前10条
    '''
    last_id = request.args.get('last_id')
    if not last_id :
        blogs = db_session.query(SmallBlog).order_by(
            # 根据Id排序
            desc(SmallBlog.id)
        ).limit(10)
    else:

        blogs = db_session.query(SmallBlog).filter(
            # 加入条件 查询id小于输入的编号
            SmallBlog.id < int(last_id)
        ).order_by(
            # 根据id desc 降序排序
            desc(SmallBlog.id)
        ).limit(10)
    
    return jsonify({'code': 1, 'blogs': [blog.to_dict() for blog in blogs]})
