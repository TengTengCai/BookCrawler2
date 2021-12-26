#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/12/26 2:18 下午
# @Author  : TianJun
# @File    : db_controller.py
# @Software: PyCharm
import logging
from random import randint

from pymongo import MongoClient

logger = logging.getLogger(__name__)


class MyDataBase(object):
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.books = self.client.book.books
        self.urls = self.client.book.urls

    def insert_book(self, data):
        try:
            self.books.insert_one(data)  # 插入数据
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
