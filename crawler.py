#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/12/26 2:16 下午
# @Author  : TianJun
# @File    : crawler.py
# @Software: PyCharm
import logging
import os.path
import pickle
import re
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

import numpy as np
import requests
from cv2 import cv2
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup


from db_controller import MongoDataBase, Book

logger = logging.getLogger(__name__)


class BookCrawler(Thread):
    def __init__(self, mongo_db: MongoDataBase, remote_uri=''):
        super().__init__()
        self.mongo_db = mongo_db
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")
        if remote_uri:
            self.driver = webdriver.Remote(remote_uri, options=self.options)
        else:
            self.driver = webdriver.Chrome(options=self.options)

    def is_login(self):
        p = re.compile(r"login\.dangdang\.com")
        current_url = self.driver.current_url
        if p.search(current_url):
            return True
        return False

    def do_baidu_login(self):
        baidu = self.driver.find_element(By.XPATH, "/html/body/div/div[2]/div/div/div[2]/a[5]/img")
        baidu.click()
        windows = self.driver.window_handles
        self.driver.switch_to.window(windows[-1])
        self.driver.implicitly_wait(5)
        username = self.driver.find_element(
            By.XPATH, '//*[@id="TANGRAM_3__userName"]'
        )
        username.send_keys("13883884201")
        password = self.driver.find_element(
            By.XPATH, '//*[@id="TANGRAM_3__password"]'
        )
        password.send_keys("tianjun223.")
        btn = self.driver.find_element(
            By.XPATH, '//*[@id="TANGRAM_3__submit"]'
        )
        btn.click()
        vcode_body = self.driver.find_element(
            By.CLASS_NAME, 'vcode-body'
        )
        if vcode_body:
            vcode_close = self.driver.find_element(
                By.CLASS_NAME, 'vcode-close'
            )
            if vcode_close:
                vcode_close.click()
                btn.click()
        windows = self.driver.window_handles
        self.driver.switch_to.window(windows[0])
        self.driver.implicitly_wait(5)
        if not self.is_login():
            cookies = self.driver.get_cookies()
            pickle.dump(cookies, open("cookies.pkl", "wb"))

    def do_login(self):
        username = self.driver.find_element(
            By.XPATH, "/html/body/div/div[2]/div/div/div[1]/div/div/div[3]/div/div[1]/div[1]/input"
        )
        username.send_keys("13883884201")
        time.sleep(0.5)
        password = self.driver.find_element(
            By.XPATH, "/html/body/div/div[2]/div/div/div[1]/div/div/div[3]/div/div[2]/div[1]/input"
        )
        password.send_keys("tianjun223.")
        time.sleep(0.5)
        btn = self.driver.find_element(
            By.XPATH, "/html/body/div/div[2]/div/div/div[1]/div/div/div[3]/div/a"
        )
        btn.click()
        time.sleep(1)
        # 是否需要滑块验证码
        try:
            slide = self.driver.find_element(
                By.CLASS_NAME, "slideVerify"
            )
        except Exception as e:
            logger.error(e)
            return
        if slide is None:
            return
        self.sliding()

    def sliding(self):
        while True:
            bg_img_raw, s_img_raw = self.get_slide_image()
            if bg_img_raw is None or s_img_raw is None:
                self.refresh_slide()
                continue
            x = self.get_x(bg_img_raw, s_img_raw)
            logger.info(f"offset x: {x}")
            if x is None or x < 50 or x > 350:
                self.refresh_slide()
                continue
            self.sliding_btn(x)
            time.sleep(1)
            try:
                error_div = self.driver.find_element(
                    By.XPATH, "/html/body/div/div[2]/div/div/div[1]/div/div/div[3]/div/div[3]"
                )
                if error_div:
                    if len(error_div.text) > 5:
                        break
            except Exception as e:
                logger.error(e)
            if not self.is_login():
                cookies = self.driver.get_cookies()
                pickle.dump(cookies, open("cookies.pkl", "wb"))
                break

    def sliding_btn(self, x):
        action_chains = webdriver.ActionChains(self.driver)
        btn = self.driver.find_element(By.ID, "sliderBtn")
        action_chains.click_and_hold(btn)
        action_chains.pause(1)
        action_chains.move_by_offset(x-36, 0)
        action_chains.release()
        action_chains.perform()

    def get_slide_image(self):
        bg_img = self.driver.find_element(
            By.ID, "bgImg"
        ).get_attribute("src")
        s_img = self.driver.find_element(
            By.ID, "simg"
        ).get_attribute("src")
        if bg_img is None or s_img is None:
            return None, None
        bg_img_resp = requests.get(bg_img, stream=True)
        s_img_resp = requests.get(s_img, stream=True)
        if bg_img_resp.status_code == 200 and s_img_resp.status_code == 200:
            return bg_img_resp.content, s_img_resp.content
        else:
            return None, None

    def refresh_slide(self):
        btn = self.driver.find_element(By.ID, "sliderRefresh")
        if btn:
            btn.click()

    @staticmethod
    def get_x(bg_img_raw, s_img_raw):
        bg_img_np = np.fromstring(bg_img_raw, np.uint8)
        s_img_np = np.fromstring(s_img_raw, np.uint8)
        bg_img = cv2.imdecode(bg_img_np, cv2.IMREAD_COLOR)
        s_img = cv2.imdecode(s_img_np, cv2.IMREAD_COLOR)

        ret, bg_img = cv2.threshold(bg_img, 50, 255, cv2.THRESH_BINARY)
        kernel = np.ones((10, 10), np.uint8)
        bg_img = cv2.morphologyEx(bg_img, cv2.MORPH_CLOSE, kernel)
        bg_img = cv2.morphologyEx(bg_img, cv2.MORPH_OPEN, kernel)

        ret, s_img = cv2.threshold(s_img, 254, 255, cv2.THRESH_BINARY)

        bg_edge = cv2.Canny(bg_img, 100, 200)
        s_edge = cv2.Canny(s_img, 100, 200)
        res = cv2.matchTemplate(bg_edge, s_edge, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)  # 寻找最优匹配
        x, _ = max_loc
        return x

    def get_url(self):
        # return "http://product.dangdang.com/29333681.html"
        url = self.mongo_db.get_url()
        if url is None:
            url = "http://book.dangdang.com/children"
            # url = "http://login.dangdang.com/"
        return url

    def put_url(self, url_list):
        with ThreadPoolExecutor(max_workers=128) as executor:
            for i in url_list:
                executor.submit(self.mongo_db.add_url, i)

    def load_page(self, url):
        self.driver.get(url)
        if self.is_login():
            if os.path.exists("cookies.pkl"):
                cookies = pickle.load(open("cookies.pkl", "rb"))
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.error(e)
            self.driver.get(url)
        if self.is_login():
            self.do_login()
        if self.is_login():
            self.do_baidu_login()
        self.driver.implicitly_wait(5)
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
        breadcrumb_div = soup.find("div", {"id": "breadcrumb"})
        if breadcrumb_div is None:
            return
        breadcrumb = breadcrumb_div.get_text(strip=True)
        if "童书" not in str(breadcrumb):  # 判断是否是属于童书
            return
        product_main = soup.find("div", {"class": "product_main"})
        if product_main is None:
            return
        book_name_div = soup.find("div", {"class": "name_info"})
        if book_name_div is None:
            return
        book = Book(
            url=url,
            name=book_name_div.h1.get_text(strip=True),
            introduction=soup.find("span", {"class": "head_title_name"}).get_text(strip=True)
        )
        big_pic = soup.find("div", {"class": "big_pic"}).img['src']
        if big_pic is None:
            return
        p = re.compile(r'^//')
        if p.match(big_pic):
            big_pic = f"http:{big_pic}"
        book.image_url = big_pic
        book_type = soup.find("li", {"id": "detail-category-path"}).get_text(strip=True)
        if book_type is None:
            book_type = soup.find("div", {"class": "breadcrumb"}).get_text(strip=True),
        book.book_type = book_type.replace("所属分类：", "")
        author = soup.find("span", {"id": "author"})
        if author is None:
            book.author = ""
        else:
            book.author = soup.find("span", {"id": "author"}).text.replace("作者:", "")
        messbox = soup.find("div", {"class": "messbox_info"})
        for item in messbox:
            if "出版社" in str(item.text):
                book.publishing = item.get_text(strip=True).replace("出版社:", "")
            elif "出版时间" in str(item):
                book.publishing_time = item.get_text(strip=True).replace("出版时间:", "")
        book.price = soup.find("p", {"id": "dd-price"}).get_text(strip=True).replace("¥", "")
        book.original_price = soup.find("div", {"id": "original-price"}).get_text(strip=True).replace("¥", "")

        editors_choice = soup.find("div", {"id": "abstract"})
        if editors_choice is None:
            book.editors_choice = ""
        else:
            book.editors_choice = editors_choice.find("div", {"class": "descrip"}).get_text(strip=True)

        content_validity = soup.find("div", {"id": "content"})
        if content_validity is None:
            book.content_validity = ""
        else:
            book.content_validity = content_validity.find("div", {"class": "descrip"}).get_text(strip=True)

        about_author = soup.find("div", {"id": "authorIntroduction"})
        if about_author is None:
            book.about_author = ""
        else:
            book.about_author = about_author.find("div", {"class": "descrip"}).get_text(strip=True)

        catalog = soup.find("textarea", {"id": "catalog-textarea"})
        if catalog is None:
            catalog2 = soup.find("div", {"id": "catalog"})
            if catalog2 is None:
                book.catalog = ""
            else:
                descrip = catalog2.find("div", {"class": "descrip"})
                if descrip:
                    book.catalog = descrip.get_text(strip=True)
        else:
            book.catalog = catalog.get_text(strip=True)

        media_reviews = soup.find("div", {"id": "mediaFeedback"})
        if media_reviews is None:
            book.media_reviews = ""
        else:
            book.media_reviews = media_reviews.get_text()
        return book

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
            "href": re.compile(r'category\.dangdang\.com/cp01\.41\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.html')
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
                self.mongo_db.update_url(book_url)
                continue

            self.mongo_db.update_url(book_url)

            book = self.parser(book_url)
            if book is not None:
                self.mongo_db.insert_book(book)
                logger.info(f"From URL {book_url} Insert Book {book}.")
            url_list = self.get_useful_url()
            self.put_url(url_list)
