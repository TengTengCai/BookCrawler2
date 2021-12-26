#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/12/26 2:16 下午
# @Author  : TianJun
# @File    : crawler.py
# @Software: PyCharm
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Thread

from selenium import webdriver
from bs4 import BeautifulSoup

from db_controller import MyDataBase

logger = logging.getLogger(__name__)


@dataclass
class Book(object):
    url: str  # 图书URL
    image_url: str  # 图书的图片URL

    name: str  # 图书名
    book_type: str  # 图书类型
    author: str  # 作者
    introduction: str  # 介绍
    publishing: str  # 出版社
    publishing_time: str  # 出版时间
    price: float  # 当当价格
    original_price: float  # 原价

    editors_choice: str  # 编辑推荐
    content_validity: str  # 内容简介
    about_author: str  # 作者简介
    catalog: str  # 目录
    media_reviews: str  # 媒体评价


class BookCrawler(Thread):
    def __init__(self, db_uri):
        super().__init__()
        self.database = MyDataBase(db_uri)
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.options)

    def get_url(self):
        url = self.database.get_url()
        if url is None:
            url = "http://book.dangdang.com/"
        return url

    def put_url(self):
        pass

    def load_page(self, url):
        self.driver.get(url)
        time.sleep(1)
        self.driver.refresh()
        js = f"""
let scrollHeight = Math.max(
  document.body.scrollHeight, document.documentElement.scrollHeight,
  document.body.offsetHeight, document.documentElement.offsetHeight,
  document.body.clientHeight, document.documentElement.clientHeight
);

return scrollHeight;
"""
        max_scroll_height = self.driver.execute_script(js)
        for step in range(0, max_scroll_height, 100):
            js = f"var q=document.documentElement.scrollTop={step}"  # 浏览器执行的js代码 向下滑动100000xp
            self.driver.execute_script(js)  # 运行脚本
            time.sleep(0.05)  # 休眠等待浏览器执行
        page_source = self.driver.page_source
        # logger.debug(f"Status {self.driver.} Request {}")
        return page_source

    def parser(self, url):
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, "lxml")
        product_main = soup.find("div", {"class": "product_main"})
        if product_main is None:
            return
        book_name_div = soup.find("div", {"class": "name_info"})
        if book_name_div is None:
            return
        book_dict = {
            "url": url,
            "name": book_name_div.h1.get_text(strip=True),
            "introduction": soup.find("span", {"class": "head_title_name"}).get_text(strip=True)
        }
        big_pic = soup.find("div", {"class": "big_pic"}).img['src']
        p = re.compile(r'^//')
        if p.match(big_pic):
            big_pic = f"http:{big_pic}"
        book_dict["image_url"] = big_pic
        book_type = soup.find("li", {"id": "detail-category-path"}).get_text(strip=True)
        if book_type is None:
            book_type = soup.find("div", {"class": "breadcrumb"}).get_text(strip=True),
        book_dict['book_type'] = book_type.replace("所属分类：", "")
        author = soup.find("span", {"id": "author"})
        if author is None:
            book_dict['author'] = ""
        else:
            book_dict['author'] = soup.find("span", {"id": "author"}).text.replace("作者:", "")
        messbox = soup.find("div", {"class": "messbox_info"})
        for item in messbox:
            if "出版社" in str(item.text):
                book_dict['publishing'] = item.get_text(strip=True).replace("出版社:", "")
            elif "出版时间" in str(item):
                book_dict['publishing_time'] = item.get_text(strip=True).replace("出版时间:", "")
        book_dict['price'] = soup.find("p", {"id": "dd-price"}).get_text(strip=True).replace("¥", "")
        book_dict['original_price'] = soup.find("div", {"id": "original-price"}).get_text(strip=True).replace("¥", "")

        editors_choice = soup.find("div", {"id": "abstract"})
        if editors_choice is None:
            book_dict['editors_choice'] = ""
        else:
            book_dict['editors_choice'] = editors_choice.find("div", {"class": "descrip"}).get_text(strip=True)

        content_validity = soup.find("div", {"id": "content"})
        if content_validity is None:
            book_dict['content_validity'] = ""
        else:
            book_dict['content_validity'] = content_validity.find("div", {"class": "descrip"}).get_text(strip=True)

        about_author = soup.find("div", {"id": "authorIntroduction"})
        if about_author is None:
            book_dict['about_author'] = ""
        else:
            book_dict['about_author'] = about_author.find("div", {"class": "descrip"}).get_text(strip=True)

        catalog = soup.find("textarea", {"id": "catalog-textarea"})
        if catalog is None:
            catalog2 = soup.find("div", {"id": "catalog"})
            if catalog2 is None:
                book_dict['catalog'] = ""
            else:
                book_dict['catalog'] = catalog2.find("div", {"class": "descrip"}).get_text(strip=True)
        else:
            book_dict['catalog'] = catalog.get_text(strip=True)

        media_reviews = soup.find("div", {"id": "mediaFeedback"})
        if media_reviews is None:
            book_dict['media_reviews'] = ""
        else:
            book_dict['media_reviews'] = media_reviews.get_text()
        return book_dict

    def get_useful_url(self):
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, "lxml")

        url_list = []  # 初始化URL列表对象

        # 通过正则表达式进行第一次筛选，选出有书籍ID的URL
        for link in soup.find_all('a', {"href": re.compile(r'^[\d](.html)?')}):
            href = str(link.get('href')).split("#")[0]
            href = href.replace("/", "")
            if len(href) < 30:
                if "javascript" not in href:
                    url = "http://product.dangdang.com/" + href
                    url_list.append(url)

        for link in soup.find_all('a', {"href": re.compile(r'^/[\d](.html)?')}):
            href = str(link.get('href')).split("#")[0]
            url = "http://product.dangdang.com" + href
            url_list.append(url)

        for link in soup.find_all('a', {"href": re.compile(r'product\.dangdang\.com/\d{6,10}\.html')}):
            href = link.get('href')
            if "http" not in href:
                href = f"http:{href}"
            url_list.append(href)

        for link in soup.find_all('a', {"href": re.compile(r'book\.dangdang\.com/\d{2}\.\d{2}\.htm')}):
            href = link.get('href')
            url_list.append(href)

        for link in soup.find_all('a', {
            "href": re.compile(r'category\.dangdang\.com/cp\d{2}\.\d{2}.\d{2}.\d{2}.\d{2}.\d{2}.html')
        }):
            href = link.get('href')
            url_list.append(href)
        # 消除列表中重复的URL
        url_list = set(url_list)
        return list(url_list)

    def run(self):
        while True:
            book_url = self.get_url()
            try:
                self.load_page(book_url)
                logger.info(f"Load Page {book_url} Success.")
            except Exception as e:
                logger.exception(e)
                logger.error(f"Load Page {book_url} Fail.")
                self.driver.quit()
                self.driver = webdriver.Chrome(options=self.options)
                self.database.update_url(book_url)
                continue

            self.database.update_url(book_url)

            book = self.parser(book_url)
            if book is not None:
                self.database.insert_book(book)
                logger.info(f"From URL {book_url} Insert Book {book}.")
            url_list = self.get_useful_url()
            with ThreadPoolExecutor(max_workers=128) as executor:
                for i in url_list:
                    executor.submit(self.database.add_url, i)

    pass
