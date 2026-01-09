import random
import requests
from bs4 import BeautifulSoup
from utils import write_head, write2csv
from config import HEADERS,COOKIES
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from utils import read_csv

class GetUpVideoInfo():
    def __init__(self):
        self.upListFile = '../data/upList.csv'
        self.driver = webdriver.Chrome()


    def get_upList(self):
        self.upList = read_csv(self.upListFile)

    def get_allUpVideo_Info(self):
        for up in self.upList[1:31]:
            self.get_upVideoInfo(up)
        self.driver.quit()

    def get_upVideoList(self,upID, category):
        url = f'https://space.bilibili.com/{upID}/video?&order={category}'

        self.driver.get(url)

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
        ul = self.driver.find_element(By.XPATH, '//*[@id="submit-video-list"]/ul[1]')
        lis = ul.find_elements(By.XPATH, "li")


        BV_videos = []
        for li in lis:
            BV_videos.append(li.get_attribute("data-aid"))

        if category == 'click':
            return BV_videos[:10]
        return BV_videos

    def get_upVideoInfo(self, up):
        pubdate = 'pubdate'
        click = 'click'
        upName, upID, upurl = up

        upPubdateVideoInfo = f'../data/upVideos/{upName}_upPubdateVideoInfo.csv'
        upClickVideoInfo = f'../data/upVideos/{upName}_upClickVideoInfo.csv'
        BV_pubdate = self.get_upVideoList(upID, pubdate)
        BV_click = self.get_upVideoList(upID, click)


        write_head(upPubdateVideoInfo,['title','bvID','tags'])
        for bvID in BV_pubdate:
            url = f'https://www.bilibili.com/video/{bvID}/'
            responses = requests.get(url, headers=HEADERS, cookies=COOKIES)
            time.sleep(random.randint(1, 3))
            html_video = BeautifulSoup(responses.text, 'html.parser')
            try:
                title = html_video.select('.video-title')[0].get_text()
            except:
                continue
            tags = [i.get_text() for i in html_video.select('.tag') if i.get_text() != '']
            row = [title, bvID, ','.join(tags)]
            write2csv(upPubdateVideoInfo, row)

        write_head(upClickVideoInfo, ['title', 'bvID','views', 'tags'])
        for bvID in BV_click:
            url = f'https://www.bilibili.com/video/{bvID}/'
            responses = requests.get(url, headers=HEADERS, cookies=COOKIES)
            time.sleep(random.randint(1,3))
            html_video = BeautifulSoup(responses.text, 'html.parser')
            try:
                title = html_video.select('.video-title')[0].get_text()
                views = html_video.select('.view-text')[0].get_text()
            except:
                continue
            tags = [i.get_text() for i in html_video.select('.tag') if i.get_text() != '']
            row = [title, bvID, views, ','.join(tags)]
            write2csv(upClickVideoInfo, row)

    def run(self):
        self.get_upList()
        self.get_allUpVideo_Info()

if __name__ == '__main__':
    getUpVideoIndo = GetUpVideoInfo()
    getUpVideoIndo.run()