'''
获取过去一周的观看历史
'''

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Generator

from crawler import BiliCrawler
from config import BiliAPI, DATA_DIR
from video_info import VideoInfo
from utils import timestamp_to_datetime, write2csv, write_head


class HistoryVideo(BiliCrawler):
    '''
    观看历史爬取类
    '''

    def __init__(self):
        super().__init__()
        self.video_info = VideoInfo()
        self.data_file = os.path.join(DATA_DIR, 'history_videos.csv')

    def get_week_start_timestamp(self) -> int:
        """
        获取一周前的时间戳
        Returns:
            int: 时间戳
        """
        week_age = datetime.now() - timedelta(days=7)
        return int(week_age.timestamp())
    
    def get_history(self, max_ts:int=0, view_at:int=0, business:str='') -> Optional[dict]:
        """
        获取观看历史(单页)
        Args:
            max_ts: 最大时间戳(用于翻页)
            view_at: 观看时间(用于翻页)
            business: 业务类型
        Returns:
            dict: 历史记录数据
        """
        params = {
            'max': max_ts,
            'view_at': view_at,
            'business': business,
            'ps': 20
        }

        resp = self._request(BiliAPI.HISTORY, params=params)

        if resp.get('code') != 0:
            print(f"获取历史记录失败: {resp.get('message')}")
            return None
    
        return resp['data']
    
    def iter_history(self, start_ts:int=None) -> Generator[dict, None, None]:
        """
        迭代获取历史记录
        Args:
            start_ts: 起始时间戳(只获取在此时间之后的记录)
        Yields:
            dict: 单条历史记录
        """
        max_ts = 0
        view_at = 0

        while True:
            data = self.get_history(max_ts=max_ts, view_at=view_at)

            # 如果没有数据, 或者数据list为[], 直接跳出while
            if not data or not data.get('list'):
                break
        
            for item in data['list']:
                # 只处理视频
                if item.get('history', {}).get('business') != 'archive':
                    continue

                item_view_at = item.get('view_at', 0)

                # 如果记录时间早于起始时间, 停止迭代
                if start_ts and item_view_at < start_ts:
                    return
                
                yield item

            # 获取下一页的游标
            cursor = data.get('cursor', {})
            max_ts = cursor.get('max', 0)
            view_at = cursor.get('view_at', 0)

            # 没有数据
            if max_ts == 0:
                break

            # 避免请求过快
            time.sleep(0.5)

    
    def get_week_history(self, include_detail: bool = False, 
                          include_comments: bool = False) -> list:
        """
        获取过去一周的观看历史
        Args:
            include_detail: 是否获取视频详情(时长、点赞等)
            include_comments: 是否获取评论(评论API限制较严，建议单独获取)
        Returns:
            list: 历史记录列表
        """
        import random
        
        week_start = self.get_week_start_timestamp()
        history_list = []
        
        print(f"正在获取过去一周的观看历史...")
        print(f"起始时间: {timestamp_to_datetime(week_start)}")
        if include_detail:
            if include_comments:
                print("⚠️ 将获取评论，可能会因反爬限制而变慢...")
            else:
                print("📝 不获取评论（可设置 include_comments=True 开启）")
        
        for item in self.iter_history(start_ts=week_start):
            history = item.get('history', {})
            
            record = {
                'bvid': history.get('bvid'),
                'title': item.get('title'),
                'author_name': item.get('author_name'),
                'author_mid': item.get('author_mid'),
                'view_at': item.get('view_at'),
                'view_at_str': timestamp_to_datetime(item.get('view_at', 0)),
                'progress': item.get('progress', 0),  # 观看进度(秒)
                'duration': item.get('duration', 0),  # 视频时长
                'cover': item.get('cover'),
            }
            
            # 获取更多视频详情
            if include_detail and record['bvid']:
                detail = self.video_info.get_full_video_details(
                    bvid=record['bvid'],
                    include_comments=include_comments,
                    comment_count=10
                )
                if detail:
                    record['stat'] = detail.get('stat')
                    record['tags'] = [t['tag_name'] for t in detail.get('tags', [])]
                    record['desc'] = detail.get('desc', '')
                    if include_comments:
                        record['top_comments'] = detail.get('top_comments', [])
                
                # 避免请求过快，使用随机延迟
                # 如果包含评论，延迟更长
                if include_comments:
                    time.sleep(random.uniform(2.0, 3.5))
                else:
                    time.sleep(random.uniform(0.3, 0.8))
            
            history_list.append(record)
            print(f"  已获取: {record['title'][:30]}...")
        
        print(f"\n共获取 {len(history_list)} 条观看记录")
        return history_list
    

    def save_history(self, history_list: list = None, include_detail: bool = False) -> bool:
        """
        保存观看历史到CSV
        Args:
            history_list: 历史记录列表
            include_detail: 是否包含详情
        Returns:
            bool: 是否成功
        """
        if history_list is None:
            history_list = self.get_week_history(include_detail=include_detail)
        
        if not history_list:
            return False
        
        # 写入表头
        if include_detail:
            heads = ['标题', 'BV号', 'UP主', '观看时间', '观看进度', '时长', 
                     '播放', '点赞', '投币', '收藏', '标签', '简介']
        else:
            heads = ['标题', 'BV号', 'UP主', '观看时间', '观看进度', '时长']
        
        # 删除已有文件重新写入
        if os.path.exists(self.data_file):
            os.remove(self.data_file)
        
        write_head(self.data_file, heads)
        
        for record in history_list:
            duration_str = self.format_duration(record.get('duration', 0))
            progress_str = self.format_duration(record.get('progress', 0))
            
            if include_detail:
                stat = record.get('stat', {})
                row = [
                    record['title'],
                    record['bvid'],
                    record['author_name'],
                    record['view_at_str'],
                    progress_str,
                    duration_str,
                    stat.get('view', ''),
                    stat.get('like', ''),
                    stat.get('coin', ''),
                    stat.get('favorite', ''),
                    ', '.join(record.get('tags', [])),
                    record.get('desc', '')[:100],  # 限制简介长度
                ]
            else:
                row = [
                    record['title'],
                    record['bvid'],
                    record['author_name'],
                    record['view_at_str'],
                    progress_str,
                    duration_str,
                ]
            
            write2csv(self.data_file, row)
        
        print(f"✓ 观看历史已保存到: {self.data_file}")
        return True
    

if __name__ == '__main__':
    history = HistoryVideo()
    
    # 获取并保存过去一周的观看历史（包含详情）
    # include_comments=False 避免触发评论API的反爬限制
    # 如需获取评论，设置 include_comments=True（速度会变慢）
    records = history.get_week_history(include_detail=True, include_comments=False)
    history.save_history(records, include_detail=True)