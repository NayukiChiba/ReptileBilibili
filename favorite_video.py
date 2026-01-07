# -*- coding: utf-8 -*-
'''
B站爬虫 - 收藏夹模块
获取所有收藏的视频
'''

import os
import time
from typing import Optional, List

from crawler import BiliCrawler
from config import BiliAPI, DATA_DIR
from utils import write_head, write2csv
from video_info import VideoInfo


class FavoriteVideo(BiliCrawler):
    '''收藏视频爬取类'''
    
    def __init__(self):
        super().__init__()
        self.video_info = VideoInfo()
        self.data_file = os.path.join(DATA_DIR, 'favorite_videos.csv')
        self.folder_dir = os.path.join(DATA_DIR, 'favorites')
        
        # 确保目录存在
        if not os.path.exists(self.folder_dir):
            os.makedirs(self.folder_dir)
    
    def get_favorite_folders(self, mid: int = None) -> List[dict]:
        '''
        获取用户的收藏夹列表
        
        :param mid: 用户UID
        :return: 收藏夹列表
        '''
        if mid is None:
            mid = self.get_mid()
        
        params = {
            'up_mid': mid,
        }
        
        resp = self._request(BiliAPI.FAVORITE_LIST, params=params)
        
        if resp.get('code') != 0:
            print(f'获取收藏夹列表失败: {resp.get('message')}')
            return []
        
        folders = []
        for folder in resp.get('data', {}).get('list', []) or []:
            folders.append({
                'id': folder.get('id'),
                'fid': folder.get('fid'),
                'title': folder.get('title'),
                'media_count': folder.get('media_count', 0),
            })
        
        return folders
    
    def get_folder_content(self, folder_id: int, page: int = 1, 
                           page_size: int = 20) -> Optional[dict]:
        '''
        获取收藏夹内容(单页)
        
        :param folder_id: 收藏夹ID
        :param page: 页码
        :param page_size: 每页数量
        :return: 收藏夹内容
        '''
        params = {
            'media_id': folder_id,
            'pn': page,
            'ps': min(page_size, 40),
            'platform': 'web',
        }
        
        resp = self._request(BiliAPI.FAVORITE_RESOURCE, params=params)
        
        if resp.get('code') != 0:
            print(f'获取收藏夹内容失败: {resp.get('message')}')
            return None
        
        return resp['data']
    
    def get_all_folder_videos(self, folder_id: int) -> List[dict]:
        '''
        获取收藏夹中所有视频
        
        :param folder_id: 收藏夹ID
        :return: 视频列表
        '''
        videos = []
        page = 1
        
        while True:
            data = self.get_folder_content(folder_id, page=page)
            if not data or not data.get('medias'):
                break
            
            for media in data['medias']:
                # 只处理视频类型
                if media.get('type') != 2:
                    continue
                
                videos.append({
                    'bvid': media.get('bvid'),
                    'id': media.get('id'),
                    'title': media.get('title'),
                    'cover': media.get('cover'),
                    'intro': media.get('intro', ''),
                    'duration': media.get('duration', 0),
                    'upper': {
                        'mid': media.get('upper', {}).get('mid'),
                        'name': media.get('upper', {}).get('name'),
                    },
                    'cnt_info': {
                        'play': media.get('cnt_info', {}).get('play', 0),
                        'danmaku': media.get('cnt_info', {}).get('danmaku', 0),
                        'collect': media.get('cnt_info', {}).get('collect', 0),
                    },
                    'fav_time': media.get('fav_time', 0),
                })
            
            # 检查是否还有更多
            if not data.get('has_more'):
                break
            
            page += 1
            time.sleep(0.5)
        
        return videos
    
    def get_all_favorites(self, include_detail: bool = False) -> dict:
        '''
        获取所有收藏夹的所有视频
        
        :param include_detail: 是否获取视频详情
        :return: {folder_title: [videos]}
        '''
        folders = self.get_favorite_folders()
        all_favorites = {}
        
        print('正在获取收藏夹内容...')
        
        for folder in folders:
            folder_title = folder['title']
            print(f'\n正在获取收藏夹: {folder_title} ({folder['media_count']}个视频)')
            
            videos = self.get_all_folder_videos(folder['id'])
            
            # 获取详情
            if include_detail:
                detailed_videos = []
                for i, v in enumerate(videos):
                    print(f'  [{i+1}/{len(videos)}] {v['title'][:30]}...')
                    
                    detail = self.video_info.get_full_video_detail(
                        bvid=v['bvid'],
                        include_comments=True,
                        comment_count=10
                    )
                    if detail:
                        # 合并信息
                        v.update({
                            'stat': detail.get('stat'),
                            'tags': detail.get('tags'),
                            'desc': detail.get('desc'),
                            'top_comments': detail.get('top_comments'),
                        })
                    detailed_videos.append(v)
                    time.sleep(0.3)
                
                videos = detailed_videos
            
            all_favorites[folder_title] = videos
            print(f'  完成,共 {len(videos)} 个视频')
        
        return all_favorites
    
    def save_all_favorites(self, favorites: dict = None, 
                           include_detail: bool = False) -> bool:
        '''
        保存所有收藏到文件
        
        :param favorites: 收藏数据
        :param include_detail: 是否包含详情
        :return: 是否成功
        '''
        if favorites is None:
            favorites = self.get_all_favorites(include_detail=include_detail)
        
        if not favorites:
            return False
        
        # 汇总所有视频到一个文件
        if os.path.exists(self.data_file):
            os.remove(self.data_file)
        
        if include_detail:
            heads = ['收藏夹', '标题', 'BV号', 'UP主', '时长', 
                     '播放', '点赞', '投币', '收藏', '标签']
        else:
            heads = ['收藏夹', '标题', 'BV号', 'UP主', '时长', '播放']
        
        write_head(self.data_file, heads)
        
        total_count = 0
        for folder_name, videos in favorites.items():
            for v in videos:
                duration_str = self.format_duration(v.get('duration', 0))
                
                if include_detail:
                    stat = v.get('stat', {}) or v.get('cnt_info', {})
                    tags = [t['tag_name'] for t in v.get('tags', [])] if v.get('tags') else []
                    row = [
                        folder_name,
                        v.get('title', ''),
                        v.get('bvid', ''),
                        v.get('upper', {}).get('name', ''),
                        duration_str,
                        stat.get('view', stat.get('play', '')),
                        stat.get('like', ''),
                        stat.get('coin', ''),
                        stat.get('favorite', stat.get('collect', '')),
                        ', '.join(tags),
                    ]
                else:
                    row = [
                        folder_name,
                        v.get('title', ''),
                        v.get('bvid', ''),
                        v.get('upper', {}).get('name', ''),
                        duration_str,
                        v.get('cnt_info', {}).get('play', ''),
                    ]
                
                write2csv(self.data_file, row)
                total_count += 1
            
            # 同时保存到单独的文件夹文件
            safe_name = ''.join(c for c in folder_name if c.isalnum() or c in (' ', '_', '-')).strip()
            folder_file = os.path.join(self.folder_dir, f'{safe_name}.csv')
            
            if os.path.exists(folder_file):
                os.remove(folder_file)
            
            write_head(folder_file, heads[1:])  # 不需要收藏夹列
            
            for v in videos:
                duration_str = self.format_duration(v.get('duration', 0))
                
                if include_detail:
                    stat = v.get('stat', {}) or v.get('cnt_info', {})
                    tags = [t['tag_name'] for t in v.get('tags', [])] if v.get('tags') else []
                    row = [
                        v.get('title', ''),
                        v.get('bvid', ''),
                        v.get('upper', {}).get('name', ''),
                        duration_str,
                        stat.get('view', stat.get('play', '')),
                        stat.get('like', ''),
                        stat.get('coin', ''),
                        stat.get('favorite', stat.get('collect', '')),
                        ', '.join(tags),
                    ]
                else:
                    row = [
                        v.get('title', ''),
                        v.get('bvid', ''),
                        v.get('upper', {}).get('name', ''),
                        duration_str,
                        v.get('cnt_info', {}).get('play', ''),
                    ]
                
                write2csv(folder_file, row)
        
        print(f'\n✓ 共 {total_count} 个收藏视频已保存')
        print(f'  汇总文件: {self.data_file}')
        print(f'  分类文件: {self.folder_dir}')
        return True


if __name__ == '__main__':
    fav = FavoriteVideo()
    
    # 获取所有收藏夹列表
    folders = fav.get_favorite_folders()
    print(f'共 {len(folders)} 个收藏夹:')
    for f in folders:
        print(f'  - {f['title']}: {f['media_count']}个视频')
    
    # 获取并保存所有收藏(不包含详情,速度较快)
    # fav.save_all_favorites(include_detail=False)
    
    # 获取并保存所有收藏(包含详情)
    # fav.save_all_favorites(include_detail=True)
