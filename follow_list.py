# -*- coding: utf-8 -*-
"""
B站爬虫 - 关注UP主模块
获取关注列表及UP主的视频信息
"""

import os
import time
from typing import Optional, List

from crawler import BiliCrawler
from config import BiliAPI, DATA_DIR
from utils import write_head, write2csv, format_number
from video_info import VideoInfo


class FollowList(BiliCrawler):
    """关注列表爬取类"""
    
    def __init__(self):
        super().__init__()
        self.video_info = VideoInfo()
        self.follow_file = os.path.join(DATA_DIR, 'follow_list.csv')
        self.up_video_dir = os.path.join(DATA_DIR, 'up_videos')
        
        # 确保目录存在
        if not os.path.exists(self.up_video_dir):
            os.makedirs(self.up_video_dir)
    
    def get_follow_list(self, mid: int = None, page: int = 1, 
                        page_size: int = 50) -> Optional[dict]:
        """
        获取关注列表(单页)
        Args:
            mid: 用户UID
            page: 页码
            page_size: 每页数量(最大50)
        Returns:
            dict: 关注列表数据
        """
        if mid is None:
            mid = self.get_mid()
        
        params = {
            'vmid': mid,
            'pn': page,
            'ps': min(page_size, 50),
            'order': 'desc',
            'order_type': 'attention',  # attention=最近关注 
        }
        
        resp = self._request(BiliAPI.FOLLOW, params=params)
        
        if resp.get('code') != 0:
            print(f"获取关注列表失败: {resp.get('message')}")
            return None
        
        return resp['data']
    
    def get_all_follows(self, mid: int = None, max_count: int = None) -> List[dict]:
        """
        获取所有关注的UP主
        Args:
            mid: 用户UID
            max_count: 最大获取数量
        Returns:
            list: 关注列表
        """
        if mid is None:
            mid = self.get_mid()
        
        follows = []
        page = 1
        
        print("正在获取关注列表...")
        
        while True:
            data = self.get_follow_list(mid=mid, page=page)
            if not data or not data.get('list'):
                break
            
            for item in data['list']:
                follow_info = {
                    'mid': item.get('mid'),
                    'uname': item.get('uname'),
                    'face': item.get('face'),
                    'sign': item.get('sign', ''),
                    'official_verify': item.get('official_verify', {}).get('desc', ''),
                    'vip_type': item.get('vip', {}).get('vipType', 0),
                }
                follows.append(follow_info)
                
                if max_count and len(follows) >= max_count:
                    break
            
            if max_count and len(follows) >= max_count:
                break
            
            # 检查是否还有更多
            total = data.get('total', 0)
            if page * 50 >= total:
                break
            
            page += 1
            time.sleep(0.5)
        
        print(f"共获取 {len(follows)} 个关注的UP主")
        return follows
    
    def get_up_videos(self, mid: int, order: str = 'pubdate', 
                      count: int = 10) -> List[dict]:
        """
        获取UP主的视频列表
        Args:
            mid: UP主UID
            order: 排序方式 pubdate=最新 click=播放量
            count: 获取数量
        Returns:
            list: 视频列表
        """
        params = {
            'mid': mid,
            'order': order,
            'pn': 1,
            'ps': min(count, 50),
        }
        
        resp = self._request_wbi(BiliAPI.SPACE_VIDEO, params=params)
        
        if resp.get('code') != 0:
            print(f"获取UP主视频失败: {resp.get('message')}")
            return []
        
        videos = []
        vlist = resp.get('data', {}).get('list', {}).get('vlist', [])
        
        for v in vlist[:count]:
            videos.append({
                'bvid': v.get('bvid'),
                'aid': v.get('aid'),
                'title': v.get('title'),
                'description': v.get('description', ''),
                'length': v.get('length'),  # 格式如 "12:34"
                'play': v.get('play', 0),
                'created': v.get('created'),
                'pic': v.get('pic'),
            })
        
        return videos
    
    def get_up_videos_with_detail(self, mid: int, count: int = 10, 
                                   include_comments: bool = True) -> List[dict]:
        """
        获取UP主视频的详细信息
        Args:
            mid: UP主UID
            count: 获取数量
            include_comments: 是否包含评论
        Returns:
            list: 视频详情列表
        """
        videos = self.get_up_videos(mid=mid, order='pubdate', count=count)
        details = []
        
        for v in videos:
            detail = self.video_info.get_full_video_detail(
                bvid=v['bvid'],
                include_comments=include_comments,
                comment_count=10
            )
            if detail:
                details.append(detail)
            time.sleep(0.3)  # 避免请求过快
        
        return details
    
    def get_all_up_info(self, recent_count: int = 10, popular_count: int = 10, 
                        include_detail: bool = True) -> List[dict]:
        """
        获取所有关注UP主的信息及其视频
        Args:
            recent_count: 每个UP主最近视频数量
            popular_count: 每个UP主热门视频数量
            include_detail: 是否获取视频详情
        Returns:
            list: UP主信息及视频列表
        """
        follows = self.get_all_follows()
        result = []
        
        for i, up in enumerate(follows):
            print(f"\n[{i+1}/{len(follows)}] 获取UP主视频: {up['uname']}")
            
            # 获取最新视频
            recent_videos = self.get_up_videos(mid=up['mid'], order='pubdate', count=recent_count)
            
            # 获取热门视频
            popular_videos = self.get_up_videos(mid=up['mid'], order='click', count=popular_count)
            
            # 获取视频详情
            if include_detail:
                recent_details = []
                for v in recent_videos:
                    detail = self.video_info.get_full_video_detail(
                        bvid=v['bvid'],
                        include_comments=True,
                        comment_count=10
                    )
                    if detail:
                        recent_details.append(detail)
                    time.sleep(0.3)
                
                popular_details = []
                for v in popular_videos:
                    # 避免重复获取
                    if any(d['bvid'] == v['bvid'] for d in recent_details):
                        continue
                    detail = self.video_info.get_full_video_detail(
                        bvid=v['bvid'],
                        include_comments=True,
                        comment_count=10
                    )
                    if detail:
                        popular_details.append(detail)
                    time.sleep(0.3)
            else:
                recent_details = recent_videos
                popular_details = popular_videos
            
            up_info = {
                **up,
                'recent_videos': recent_details,
                'popular_videos': popular_details,
            }
            result.append(up_info)
            
            # 避免请求过快
            time.sleep(1)
        
        return result
    
    def save_follow_list(self, follows: List[dict] = None) -> bool:
        """
        保存关注列表到CSV
        Args:
            follows: 关注列表
        Returns:
            bool: 是否成功
        """
        if follows is None:
            follows = self.get_all_follows()
        
        if not follows:
            return False
        
        # 删除已有文件
        if os.path.exists(self.follow_file):
            os.remove(self.follow_file)
        
        heads = ['昵称', 'UID', '签名', '认证']
        write_head(self.follow_file, heads)
        
        for up in follows:
            row = [
                up['uname'],
                up['mid'],
                up.get('sign', '')[:50],
                up.get('official_verify', ''),
            ]
            write2csv(self.follow_file, row)
        
        print(f"✓ 关注列表已保存到: {self.follow_file}")
        return True
    
    def save_up_videos(self, up_info: dict) -> bool:
        """
        保存单个UP主的视频信息到CSV
        Args:
            up_info: UP主信息 (包含视频列表 )
        Returns:
            bool: 是否成功
        """
        uname = up_info['uname']
        # 清理文件名中的非法字符
        safe_name = "".join(c for c in uname if c.isalnum() or c in (' ', '_', '-')).strip()
        
        # 保存最新视频
        recent_file = os.path.join(self.up_video_dir, f'{safe_name}_最新视频.csv')
        if os.path.exists(recent_file):
            os.remove(recent_file)
        
        heads = ['标题', 'BV号', '时长', '播放', '点赞', '投币', '收藏', '标签']
        write_head(recent_file, heads)
        
        for v in up_info.get('recent_videos', []):
            stat = v.get('stat', {})
            tags = [t['tag_name'] for t in v.get('tags', [])] if isinstance(v.get('tags'), list) and v.get('tags') and isinstance(v['tags'][0], dict) else v.get('tags', [])
            row = [
                v.get('title', ''),
                v.get('bvid', ''),
                v.get('duration_str', v.get('length', '')),
                stat.get('view', v.get('play', '')),
                stat.get('like', ''),
                stat.get('coin', ''),
                stat.get('favorite', ''),
                ', '.join(tags) if tags else '',
            ]
            write2csv(recent_file, row)
        
        # 保存热门视频
        popular_file = os.path.join(self.up_video_dir, f'{safe_name}_热门视频.csv')
        if os.path.exists(popular_file):
            os.remove(popular_file)
        
        write_head(popular_file, heads)
        
        for v in up_info.get('popular_videos', []):
            stat = v.get('stat', {})
            tags = [t['tag_name'] for t in v.get('tags', [])] if isinstance(v.get('tags'), list) and v.get('tags') and isinstance(v['tags'][0], dict) else v.get('tags', [])
            row = [
                v.get('title', ''),
                v.get('bvid', ''),
                v.get('duration_str', v.get('length', '')),
                stat.get('view', v.get('play', '')),
                stat.get('like', ''),
                stat.get('coin', ''),
                stat.get('favorite', ''),
                ', '.join(tags) if tags else '',
            ]
            write2csv(popular_file, row)
        
        print(f"  ✓ {uname} 的视频已保存")
        return True
    
    def save_all_up_videos(self, up_list: List[dict] = None, 
                            recent_count: int = 10, 
                            popular_count: int = 10) -> bool:
        """
        保存所有UP主的视频信息
        Args:
            up_list: UP主列表 (包含视频 )
            recent_count: 最新视频数量
            popular_count: 热门视频数量
        Returns:
            bool: 是否成功
        """
        if up_list is None:
            up_list = self.get_all_up_info(
                recent_count=recent_count, 
                popular_count=popular_count,
                include_detail=True
            )
        
        if not up_list:
            return False
        
        # 保存关注列表
        self.save_follow_list(up_list)
        
        # 保存每个UP主的视频
        for up in up_list:
            self.save_up_videos(up)
        
        print(f"\n✓ 所有UP主视频已保存到: {self.up_video_dir}")
        return True


if __name__ == '__main__':
    follow = FollowList()
    
    # 获取并保存关注列表
    follows = follow.get_all_follows()
    follow.save_follow_list(follows)
    
    # 获取每个UP主的最新10个和热门10个视频
    # up_list = follow.get_all_up_info(recent_count=10, popular_count=10)
    # follow.save_all_up_videos(up_list)