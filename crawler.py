'''
爬虫基类
'''

import requests
import time
import hashlib
import urllib.parse
from functools import reduce

from config import HEADERS, REPLY_HEADERS, load_cookies, BiliAPI


class BiliCrawler:
    '''
    B站爬虫基类
    '''
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
        27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
        37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
        22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52
    ]

    def __init__(self):
        # 请求
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cookies = load_cookies()
        self._img_key = None
        self._sub_key = None

    def _request(self, url:str, params: dict=None, method: str='GET', **kwargs)->dict:
        '''
        发送请求并返回json数据
        :param 
            url: 请求的url
            params: 请求的参数
            method: 请求的方法
        :return
            dict: json数据
        '''
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, cookies=self.cookies, **kwargs)
            else:
                response = self.session.post(url, data=params, cookies=self.cookies, **kwargs)
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {'code': -1, 'message': str(e)}
        
    def _get_mixin_key(self, orig: str) -> str:
        '''
        对img_key和sub_key进行混淆
        '''
        return reduce(lambda s, i: s + orig[i], self.MIXIN_KEY_ENC_TAB, '')[:32]
    
    def _get_wbi_keys(self) -> tuple:
        '''
        获取 WBI 签名需要的img_key和sub_key
        :return
             tuple: (img_key, sub_key)
        '''
        if self._img_key and self._sub_key:
            return self._img_key, self._sub_key
        
        resp = self._request(BiliAPI.NAV_INFO)
        if resp.get('code') == 0:
            wbi_img = resp['data']['wbi_img']
            img_url = wbi_img['img_url']
            sub_url = wbi_img['sub_url']

            self._img_key = img_url.rsplit('/', 1)[1].split('.')[0]
            self._sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
        
        return self._img_key, self._sub_key
    
    def _encode_wbi(self, params: dict) -> dict:
        '''
        为请求参数生成WBI签名

        :param params: 原始请求参数
        :return: 添加了wts和w_rid的参数
        '''
        img_key, sub_key = self._get_wbi_keys()
        if not img_key or not sub_key:
            return params

        mixin_key = self._get_mixin_key(img_key + sub_key)
        curr_time = round(time.time())
        params['wts'] = curr_time

        # 按照key排序
        params = dict(sorted(params.items()))

        # 过滤特殊字符
        params = {
            key : ''.join(filter(lambda c: c not in "!'()*", str(value))) for key, value in params.items()
        }

        # 生成签名
        query = urllib.parse.urlencode(params)
        wbi_sign = hashlib.md5((query + mixin_key).encode()).hexdigest()
        params['w_rid'] = wbi_sign

        return params
    
    def _request_wbi(self, url: str, params: dict=None, **kwargs) -> dict:
        '''
        生成需要WBI签名的请求
        
        :param url: 请求url
        :param params: 原始参数

        :return: json请求数据
        '''

        if params is None:
            params = {}
        signed_params = self._encode_wbi(params=params)
        return self._request(url, params=signed_params, **kwargs)
    
    
    def _request_reply(self, url: str, params: dict = None, bvid: str = None, 
                       retry_count: int = 3, **kwargs) -> dict:
        """
        发送评论相关请求（带重试和特殊处理）
        评论API对反爬更敏感，需要特殊处理
        Args:
            url: 请求URL
            params: 请求参数  
            bvid: 视频BV号（用于设置Referer）
            retry_count: 重试次数
        Returns:
            dict: JSON响应数据
        """
        import random
        
        # 设置评论专用的 Referer
        headers = {}
        if bvid:
            headers['Referer'] = f'https://www.bilibili.com/video/{bvid}/'
        else:
            headers.update(REPLY_HEADERS)
        
        for attempt in range(retry_count):
            try:
                # 添加随机延迟，模拟真实用户行为
                delay = random.uniform(0.8, 1.5)
                time.sleep(delay)
                
                response = self.session.get(
                    url, 
                    params=params, 
                    cookies=self.cookies,
                    headers=headers,
                    **kwargs
                )
                
                # 如果是 412 错误，等待更长时间后重试
                if response.status_code == 412:
                    wait_time = (attempt + 1) * 2  # 递增等待时间
                    print(f"遇到反爬限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                if attempt < retry_count - 1:
                    print(f"请求失败，重试中 ({attempt + 1}/{retry_count})...")
                    time.sleep(1)
                else:
                    print(f"获取评论失败: {e}")
                    return {'code': -1, 'message': str(e)}
        
        return {'code': -1, 'message': '请求失败，已达到最大重试次数'}


    def get_mid(self) -> str:
        '''
        获取user的MID
        :return: 用户MID
        '''
        return self.cookies.get('DedeUserID')

    @staticmethod
    def format_duration(seconds: int) -> str:
        '''
        格式化时长
        
        :param seconds: 秒数

        :return: 格式化之后的时长字符串
        '''
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"