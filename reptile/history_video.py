import requests
from bs4 import BeautifulSoup
import json
from config import COOKIES, HEADERS,URL_HISTORY
from datetime import datetime, timedelta
from utils import write_head,write2csv
class GetHistoryVideo():
    def __init__(self):
        self.historyInfoFile = '../data/historyInfo.csv'

    def get_lastweekTimestamp(self):
        # 获取从现在算七天前的时间戳
        current_time = datetime.now()
        seven_days_ago = current_time - timedelta(days=7)
        self.timestamp = seven_days_ago.timestamp()

    def get_historyInfo(self):


        # 把这个时间戳放入url，用来请求过去一周的数据
        url = (str(int(self.timestamp))).join(URL_HISTORY.split('0'))
        responses = requests.get(url, headers=HEADERS, cookies=COOKIES)
        html = BeautifulSoup(responses.text, 'html.parser')
        data = json.loads(str(html))['data']['list']

        # 获取每条视频的title、up主、tag、观看的时间，写入csv
        heads = ['title', 'up', 'tag', 'datetime']
        write_head(self.historyInfoFile, heads)
        for item in data:
            bvID = item['history']['bvid']
            url = f'https://www.bilibili.com/video/{bvID}/'
            responses = requests.get(url, headers=HEADERS, cookies=COOKIES)
            html_video = BeautifulSoup(responses.text, 'html.parser')
            tags = [i.get_text() for i in html_video.select('.tag') if i.get_text() != '']
            row = [item['title'], item['author_name'], ' '.join(tags), str(datetime.fromtimestamp(item['view_at']))]
            write2csv(self.historyInfoFile, row)

    def run(self):
        self.get_lastweekTimestamp()
        self.get_historyInfo()

if __name__ == '__main__':
    getHistoryVideo = GetHistoryVideo()
    getHistoryVideo.run()