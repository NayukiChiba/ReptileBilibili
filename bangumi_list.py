# -*- coding: utf-8 -*-
'''
获取订阅的番剧列表
'''

import os
import time
from typing import Optional, List

from crawler import BiliCrawler
from config import BiliAPI, DATA_DIR
from utils import write_head, write2csv, timestamp_to_datetime


class BangumiList(BiliCrawler):
    '''番剧订阅爬取类'''
    
    def __init__(self):
        super().__init__()
        self.bangumi_file = os.path.join(DATA_DIR, 'bangumi_list.csv')
    
    def get_bangumi_list(self, mid: int = None, type_: int = 1, 
                          page: int = 1, page_size: int = 15) -> Optional[dict]:
        '''
        获取追番/追剧列表(单页)
        
        :param mid: 用户UID
        :param type_: 类型 1=追番 2=追剧
        :param page: 页码
        :param page_size: 每页数量(最奇30)
        :return: 追番列表数据
        '''
        if mid is None:
            mid = self.get_mid()
        
        params = {
            'vmid': mid,
            'type': type_,
            'pn': page,
            'ps': min(page_size, 30),
        }
        
        resp = self._request(BiliAPI.BANGUMI_LIST, params=params)
        
        if resp.get('code') != 0:
            print(f'获取追番列表失败: {resp.get('message')}')
            return None
        
        return resp['data']
    
    def get_all_bangumi(self, mid: int = None, type_: int = 1) -> List[dict]:
        '''
        获取所有追番/追剧
        
        :param mid: 用户UID
        :param type_: 类型 1=追番 2=追剧
        :return: 追番列表
        '''
        bangumi_list = []
        page = 1
        
        type_name = '追番' if type_ == 1 else '追剧'
        print(f'正在获取{type_name}列表...')
        
        while True:
            data = self.get_bangumi_list(mid=mid, type_=type_, page=page)
            if not data or not data.get('list'):
                break
            
            for item in data['list']:
                bangumi_info = {
                    'season_id': item.get('season_id'),
                    'media_id': item.get('media_id'),
                    'title': item.get('title'),
                    'cover': item.get('cover'),
                    'evaluate': item.get('evaluate', ''),  # 简介
                    'total_count': item.get('total_count', 0),  # 总集数
                    'progress': item.get('progress', ''),  # 观看进度
                    'is_finish': item.get('is_finish', 0),  # 是否完结
                    'areas': [a.get('name', '') for a in item.get('areas', [])],  # 地区
                    'badge': item.get('badge', ''),  # 角标(如:会员专享)
                    'rating': item.get('rating', {}).get('score', 0) if item.get('rating') else 0,
                    'rating_count': item.get('rating', {}).get('count', 0) if item.get('rating') else 0,
                    'follow_status': item.get('follow_status', 0),  # 1=想看 2=在看 3=看过
                    'follow_time': item.get('follow_time', 0),
                    'follow_time_str': timestamp_to_datetime(item.get('follow_time', 0)) if item.get('follow_time') else '',
                    'new_ep': {
                        'title': item.get('new_ep', {}).get('index_show', ''),
                        'cover': item.get('new_ep', {}).get('cover', ''),
                    },
                    'url': item.get('url', ''),
                }
                bangumi_list.append(bangumi_info)
            
            # 检查是否还有更多
            total = data.get('total', 0)
            if page * 15 >= total:
                break
            
            page += 1
            time.sleep(0.5)
        
        print(f'共获取 {len(bangumi_list)} 部{type_name}')
        return bangumi_list
    
    def get_all_subscriptions(self, mid: int = None) -> dict:
        '''
        获取所有订阅（追番+追剧）
        
        :param mid: 用户UID
        :return: {'bangumi': [], 'drama': []}
        '''
        # 获取追番
        bangumi = self.get_all_bangumi(mid=mid, type_=1)
        
        # 获取追剧
        drama = self.get_all_bangumi(mid=mid, type_=2)
        
        return {
            'bangumi': bangumi,  # 番剧
            'drama': drama,  # 国创/电视剧
        }
    
    def save_bangumi_list(self, subscriptions: dict = None) -> bool:
        '''
        保存追番追剧列表到CSV
        
        :param subscriptions: 订阅数据
        :return: 是否成功
        '''
        if subscriptions is None:
            subscriptions = self.get_all_subscriptions()
        
        # 删除已有文件
        if os.path.exists(self.bangumi_file):
            os.remove(self.bangumi_file)
        
        heads = ['类型', '标题', '评分', '总集数', '观看进度', '是否完结', 
                 '地区', '订阅时间', '简介', '链接']
        write_head(self.bangumi_file, heads)
        
        total_count = 0
        
        # 保存追番
        for b in subscriptions.get('bangumi', []):
            row = [
                '番剧',
                b.get('title', ''),
                b.get('rating', ''),
                b.get('total_count', ''),
                b.get('progress', ''),
                '是' if b.get('is_finish') else '否',
                ', '.join(b.get('areas', [])),
                b.get('follow_time_str', ''),
                b.get('evaluate', '')[:100],
                b.get('url', ''),
            ]
            write2csv(self.bangumi_file, row)
            total_count += 1
        
        # 保存追剧
        for d in subscriptions.get('drama', []):
            row = [
                '国创/电视剧',
                d.get('title', ''),
                d.get('rating', ''),
                d.get('total_count', ''),
                d.get('progress', ''),
                '是' if d.get('is_finish') else '否',
                ', '.join(d.get('areas', [])),
                d.get('follow_time_str', ''),
                d.get('evaluate', '')[:100],
                d.get('url', ''),
            ]
            write2csv(self.bangumi_file, row)
            total_count += 1
        
        print(f'\n✓ 共 {total_count} 部追番/追剧已保存到: {self.bangumi_file}')
        return True
    
    def print_bangumi_list(self, subscriptions: dict = None):
        '''
        打印追番追剧列表
        
        :param subscriptions: 订阅数据
        '''
        if subscriptions is None:
            subscriptions = self.get_all_subscriptions()
        
        print('\n' + '=' * 60)
        print('追番列表')
        print('=' * 60)
        
        for b in subscriptions.get('bangumi', []):
            status = '✓完结' if b.get('is_finish') else '更新中'
            progress = b.get('progress', '')
            rating = f'评分:{b.get('rating', 'N/A')}' if b.get('rating') else ''
            print(f'  [{status}] {b.get('title', '')} | {progress} | {rating}')
        
        print('\n' + '=' * 60)
        print('追剧列表')
        print('=' * 60)
        
        for d in subscriptions.get('drama', []):
            status = '✓完结' if d.get('is_finish') else '更新中'
            progress = d.get('progress', '')
            rating = f'评分:{d.get('rating', 'N/A')}' if d.get('rating') else ''
            print(f'  [{status}] {d.get('title', '')} | {progress} | {rating}')


if __name__ == '__main__':
    bangumi = BangumiList()
    
    # 获取并打印追番追剧列表
    subs = bangumi.get_all_subscriptions()
    bangumi.print_bangumi_list(subs)
    
    # 保存到文件
    bangumi.save_bangumi_list(subs)