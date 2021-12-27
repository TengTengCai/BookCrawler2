#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/12/26 2:18 下午
# @Author  : TianJun
# @File    : db_controller.py
# @Software: PyCharm
import logging
from dataclasses import dataclass, asdict
from random import randint

from pymongo import MongoClient

logger = logging.getLogger(__name__)


@dataclass
class Book(object):
    url: str = None  # 图书URL
    image_url: str = None  # 图书的图片URL

    name: str = None  # 图书名
    book_type: str = None  # 图书类型
    author: str = None  # 作者
    introduction: str = None  # 介绍
    publishing: str = None  # 出版社
    publishing_time: str = None  # 出版时间
    price: float = None  # 当当价格
    original_price: float = None  # 原价

    editors_choice: str = None  # 编辑推荐
    content_validity: str = None  # 内容简介
    about_author: str = None  # 作者简介
    catalog: str = None  # 目录
    media_reviews: str = None  # 媒体评价


class MyDataBase(object):
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.books = self.client.book.books
        self.urls = self.client.book.urls

    def insert_book(self, data: Book):
        try:
            self.books.insert_one(asdict(data))  # 插入数据
        except Exception as e:
            logger.exception(e)

    def add_url(self, url):
        try:
            if not self.is_exist_url(url):  # 判断是否存在
                self.urls.insert_one({'url': url, 'isExist': 'false'})  # 插入
        except Exception as e:
            logger.exception(e)

    def is_exist_url(self, url):
        try:
            result = self.urls.find_one({"url": url})  # 获取查询结果
            if result is None:
                return False  # 返回False
            else:
                return True  # 返回True
        except Exception as e:
            logger.exception(e)

    def get_url(self):
        num = randint(1, 100)  # 随机数
        try:
            result = self.urls.find({'isExist': 'false'}).skip(num).limit(1)  # 跳跃式获取数据
            return result[0]['url']  # 返回对应的URL地址
        except Exception as e:
            logger.exception(e)

    def update_url(self, url):
        try:
            self.urls.update_one({'url': url}, {'$set': {'isExist': 'true'}})  # 更新URL的状态为True表示已经爬取过了
        except Exception as e:
            logger.exception(e)
