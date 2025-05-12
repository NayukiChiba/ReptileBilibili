import re
from config import COOKIES, MID
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from utils import write_head, write2csv


class GetUpList():
    def __init__(self, mid):
        self.mid = mid
        self.driver = webdriver.Chrome()
        self.url = f'https://space.bilibili.com/{self.mid}/fans/follow/'
        self.file = '../data/upList.csv'
        self.heads = ['upName', 'upID', 'upurl']

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

    def get_upList(self):
        ul = self.driver.find_element(By.XPATH, '//*[@id="page-follows"]/div/div[2]/div[2]/div[2]/ul[1]')
        lis = ul.find_elements(By.XPATH, "li")

        for li in lis:  # //*[@id="page-follows"]/div/div[2]/div[2]/div[2]/ul[1]/li[1]/div[3]/a
            upID = ((li.find_element(By.XPATH, "div[3]/a")).get_attribute('href')).split('/')[-2]
            upName = (li.text).split()[0]
            upurl = f'https://space.bilibili.com/{upID}'
            write2csv(self.file, [upName, upID, upurl])

    def next_page(self):
        # 遍历所有页面，获取所有up主的信息）
        total = WebDriverWait(self.driver, 10).until(
            lambda x: x.find_element(By.XPATH, '//*[@id="page-follows"]/div/div[2]/div[2]/div[2]/ul[2]/span[1]'))
        number = re.findall(r"\d+", total.text)
        total = int(number[0])

        for page in range(1, total):
            try:
                # 点击翻页；如果找不到下一页则停止
                self.driver.find_element(By.LINK_TEXT, '下一页').click()
                time.sleep(2)  # 等待页面加载
                self.get_upList()
            except Exception as e:
                print(f"Failed to click next page: {e}")

    def run(self):
        write_head(self.file, self.heads)
        self.login()
        self.get_upList()
        self.next_page()
        self.driver.quit()


if __name__ == '__main__':
    getUpList = GetUpList(MID)
    getUpList.run()
