import requests
from bs4 import BeautifulSoup
import re
from config import COOKIES, MID, HEADERS
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from utils import write_head,write2csv

class GetFavoriteVideoInfo:
    def __init__(self):
        self.url = f'https://space.bilibili.com/{MID}/favlist'
        self.driver = webdriver.Chrome()
        self.file = '../data/favoriteInfo.csv'

    def login(self):
        self.driver.get(self.url)

        # selenium添加cookies
        for name, value in COOKIES.items():
            cookie_dict = {
                'domain': '.bilibili.com',
                'name': name,
                'value': value,
                "expires": '',
                'path': '/',
                'httpOnly': False,
                'HostOnly': False,
                'Secure': False
            }
            self.driver.add_cookie(cookie_dict)
        self.driver.refresh()
        time.sleep(10)

    def get_favoriteInfo(self):
        ul = self.driver.find_element(By.XPATH,'//*[@id="page-fav"]/div[1]/div[2]/div[3]/ul[1]')
        lis = ul.find_elements(By.XPATH,'li')

        for li in lis:
            bvID = li.get_attribute('data-aid')
            url = f'https://www.bilibili.com/video/{bvID}/'
            responses = requests.get(url, headers=HEADERS, cookies=COOKIES)
            html_video = BeautifulSoup(responses.text, 'html.parser')
            try:
                title = html_video.select('.video-title')[0].get_text()
            # 如果没有title说明这个视频已经不存在了
            except:
                continue
            tags = [i.get_text() for i in html_video.select('.tag') if i.get_text() != '']
            write2csv(self.file, [title, bvID, ''.join(tags)])

    def next_page(self):
        # 遍历所有页面，获取所有up主的信息）
        total = WebDriverWait(self.driver, 10).until(
            lambda x: x.find_element(By.XPATH, '//*[@id="page-fav"]/div[1]/div[2]/div[3]/ul[2]/span[1]'))
        number = re.findall(r"\d+", total.text)
        total = int(number[0])

        for page in range(1, total):
            try:
                # 点击翻页；如果找不到下一页则停止
                self.driver.find_element(By.LINK_TEXT, '下一页').click()
                time.sleep(2)  # 等待页面加载
                self.get_favoriteInfo()
            except Exception as e:
                print(f"Failed to click next page: {e}")

    def run(self):
        self.login()
        write_head(self.file, ['title', 'bvID', 'tags'])
        self.get_favoriteInfo()
        self.next_page()

if __name__ == '__main__':
    getFavoriteVideoInfo = GetFavoriteVideoInfo()
    getFavoriteVideoInfo.run()