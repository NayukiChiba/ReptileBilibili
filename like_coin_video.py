# -*- coding: utf-8 -*-
'''
B站爬虫 - 点赞投币记录模块
获取最近点赞和投币的视频
'''

import os
import time
from typing import Optional, List

from crawler import BiliCrawler
from config import BiliAPI, DATA_DIR
from utils import write_head, write2csv, timestamp_to_datetime
from video_info import VideoInfo


class LikeCoinVideo(BiliCrawler):
    '''点赞投币记录爬取类'''
    
    def __init__(self):
        super().__init__()
        self.video_info = VideoInfo()
        self.like_file = os.path.join(DATA_DIR, 'liked_videos.csv')
        self.coin_file = os.path.join(DATA_DIR, 'coined_videos.csv')
    
    def get_liked_videos(self, mid: int = None, page: int = 1, 
                         page_size: int = 30) -> Optional[dict]:
        '''
        获取点赞视频列表(单页)
        注意: B站API只返回最近点赞的视频，数量有限
        
        :param mid: 用户UID
        :param page: 页码
        :param page_size: 每页数量
        :return: 点赞视频数据
        '''
        if mid is None:
            mid = self.get_mid()
        
        params = {
            'vmid': mid,
            'pn': page,
            'ps': min(page_size, 30),
        }
        
        resp = self._request_wbi(BiliAPI.LIKE_VIDEO, params=params)
        
        if resp.get('code') != 0:
            print(f'获取点赞视频失败: {resp.get('message')}')
            return None
        
        return resp['data']
    
    def get_all_liked_videos(self, mid: int = None, max_count: int = 100) -> List[dict]:
        '''
        获取所有点赞视频（受B站API限制，可能无法获取全部历史）
        
        :param mid: 用户UID
        :param max_count: 最大获取数量
        :return: 点赞视频列表
        '''
        videos = []
        page = 1
        
        print(f'正在获取点赞视频列表(最多{max_count}个)...')
        
        while len(videos) < max_count:
            data = self.get_liked_videos(mid=mid, page=page)
            if not data or not data.get('list'):
                break
            
            for item in data['list']:
                videos.append({
                    'bvid': item.get('bvid'),
                    'aid': item.get('aid'),
                    'title': item.get('title'),
                    'pic': item.get('pic'),
                    'owner': {
                        'mid': item.get('owner', {}).get('mid'),
                        'name': item.get('owner', {}).get('name'),
                    },
                    'stat': {
                        'view': item.get('stat', {}).get('view', 0),
                        'danmaku': item.get('stat', {}).get('danmaku', 0),
                    },
                    'duration': item.get('duration', 0),
                    'pubdate': item.get('pubdate', 0),
                })
                
                if len(videos) >= max_count:
                    break
            
            page += 1
            time.sleep(0.5)
        
        print(f'共获取 {len(videos)} 个点赞视频')
        return videos
    
    def get_coined_videos(self, page: int = 1, page_size: int = 20) -> Optional[dict]:
        '''
        获取投币视频列表(单页)
        
        :param page: 页码
        :param page_size: 每页数量
        :return: 投币视频数据
        '''
        params = {
            'pn': page,
            'ps': min(page_size, 20),
        }
        
        resp = self._request(BiliAPI.COIN_VIDEO, params=params)
        
        if resp.get('code') != 0:
            print(f'获取投币视频失败: {resp.get('message')}')
            return None
        
        return resp['data']
    
    def get_all_coined_videos(self, max_count: int = 100) -> List[dict]:
        '''
        获取投币视频列表
        
        :param max_count: 最大获取数量
        :return: 投币视频列表
        '''
        videos = []
        page = 1
        
        print(f'正在获取投币视频列表(最多{max_count}个)...')
        
        while len(videos) < max_count:
            data = self.get_coined_videos(page=page)
            if not data or not data.get('list'):
                break
            
            for item in data['list']:
                videos.append({
                    'bvid': item.get('bvid'),
                    'aid': item.get('aid'),
                    'title': item.get('title'),
                    'pic': item.get('pic'),
                    'owner': {
                        'mid': item.get('owner', {}).get('mid'),
                        'name': item.get('owner', {}).get('name'),
                    },
                    'stat': {
                        'view': item.get('stat', {}).get('view', 0),
                    },
                    'duration': item.get('duration', 0),
                    'coin_count': item.get('coin_count', 0),  # 投币数量
                    'ts': item.get('ts', 0),  # 投币时间
                    'ts_str': timestamp_to_datetime(item.get('ts', 0)) if item.get('ts') else '',
                })
                
                if len(videos) >= max_count:
                    break
            
            page += 1
            time.sleep(0.5)
        
        print(f'共获取 {len(videos)} 个投币视频')
        return videos
    
    def get_videos_with_detail(self, videos: List[dict], 
                                include_comments: bool = True) -> List[dict]:
        '''
        获取视频的详细信息
        
        :param videos: 视频列表
        :param include_comments: 是否包含评论
        :return: 带详情的视频列表
        '''
        detailed = []
        
        for i, v in enumerate(videos):
            print(f'  [{i+1}/{len(videos)}] 获取详情: {v['title'][:30]}...')
            
            detail = self.video_info.get_full_video_detail(
                bvid=v['bvid'],
                include_comments=include_comments,
                comment_count=10
            )
            
            if detail:
                v.update({
                    'full_stat': detail.get('stat'),
                    'tags': detail.get('tags'),
                    'desc': detail.get('desc'),
                    'top_comments': detail.get('top_comments'),
                })
            
            detailed.append(v)
            time.sleep(0.3)
        
        return detailed
    
    def save_liked_videos(self, videos: List[dict] = None, 
                          include_detail: bool = False) -> bool:
        '''
        保存点赞视频到CSV
        
        :param videos: 点赞视频列表
        :param include_detail: 是否包含详情
        :return: 是否成功
        '''
        if videos is None:
            videos = self.get_all_liked_videos(max_count=100)
        
        if not videos:
            return False
        
        # 获取详情
        if include_detail:
            print('\n正在获取视频详情...')
            videos = self.get_videos_with_detail(videos)
        
        # 删除已有文件
        if os.path.exists(self.like_file):
            os.remove(self.like_file)
        
        if include_detail:
            heads = ['标题', 'BV号', 'UP主', '时长', '播放', '点赞', 
                     '投币', '收藏', '标签']
        else:
            heads = ['标题', 'BV号', 'UP主', '时长', '播放']
        
        write_head(self.like_file, heads)
        
        for v in videos:
            duration_str = self.format_duration(v.get('duration', 0))
            
            if include_detail:
                stat = v.get('full_stat', {}) or v.get('stat', {})
                tags = [t['tag_name'] for t in v.get('tags', [])] if v.get('tags') else []
                row = [
                    v.get('title', ''),
                    v.get('bvid', ''),
                    v.get('owner', {}).get('name', ''),
                    duration_str,
                    stat.get('view', ''),
                    stat.get('like', ''),
                    stat.get('coin', ''),
                    stat.get('favorite', ''),
                    ', '.join(tags),
                ]
            else:
                row = [
                    v.get('title', ''),
                    v.get('bvid', ''),
                    v.get('owner', {}).get('name', ''),
                    duration_str,
                    v.get('stat', {}).get('view', ''),
                ]
            
            write2csv(self.like_file, row)
        
        print(f'\n✓ 点赞视频已保存到: {self.like_file}')
        return True
    
    def save_coined_videos(self, videos: List[dict] = None, 
                           include_detail: bool = False) -> bool:
        '''
        保存投币视频到CSV
        
        :param videos: 投币视频列表
        :param include_detail: 是否包含详情
        :return: 是否成功
        '''
        if videos is None:
            videos = self.get_all_coined_videos(max_count=100)
        
        if not videos:
            return False
        
        # 获取详情
        if include_detail:
            print('\n正在获取视频详情...')
            videos = self.get_videos_with_detail(videos)
        
        # 删除已有文件
        if os.path.exists(self.coin_file):
            os.remove(self.coin_file)
        
        if include_detail:
            heads = ['标题', 'BV号', 'UP主', '投币数', '投币时间', '时长', 
                     '播放', '点赞', '投币总数', '收藏', '标签']
        else:
            heads = ['标题', 'BV号', 'UP主', '投币数', '投币时间', '时长', '播放']
        
        write_head(self.coin_file, heads)
        
        for v in videos:
            duration_str = self.format_duration(v.get('duration', 0))
            
            if include_detail:
                stat = v.get('full_stat', {}) or v.get('stat', {})
                tags = [t['tag_name'] for t in v.get('tags', [])] if v.get('tags') else []
                row = [
                    v.get('title', ''),
                    v.get('bvid', ''),
                    v.get('owner', {}).get('name', ''),
                    v.get('coin_count', ''),
                    v.get('ts_str', ''),
                    duration_str,
                    stat.get('view', ''),
                    stat.get('like', ''),
                    stat.get('coin', ''),
                    stat.get('favorite', ''),
                    ', '.join(tags),
                ]
            else:
                row = [
                    v.get('title', ''),
                    v.get('bvid', ''),
                    v.get('owner', {}).get('name', ''),
                    v.get('coin_count', ''),
                    v.get('ts_str', ''),
                    duration_str,
                    v.get('stat', {}).get('view', ''),
                ]
            
            write2csv(self.coin_file, row)
        
        print(f'\n✓ 投币视频已保存到: {self.coin_file}')
        return True
    
    def save_all(self, include_detail: bool = False) -> bool:
        '''
        保存所有点赞和投币视频
        
        :param include_detail: 是否包含详情
        :return: 是否成功
        '''
        # 获取点赞视频
        liked = self.get_all_liked_videos(max_count=100)
        self.save_liked_videos(liked, include_detail=include_detail)
        
        # 获取投币视频
        coined = self.get_all_coined_videos(max_count=100)
        self.save_coined_videos(coined, include_detail=include_detail)
        
        return True


if __name__ == '__main__':
    lc = LikeCoinVideo()
    
    # 获取并保存点赞和投币视频（不包含详情）
    lc.save_all(include_detail=False)
    
    # 获取并保存（包含详情）
    # lc.save_all(include_detail=True)
