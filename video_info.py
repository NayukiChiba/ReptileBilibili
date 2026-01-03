'''
获取一个视频的基本信息: 时长、点赞投币、评论、简介、tag
'''

from typing import Optional

from config import BiliAPI
from crawler import BiliCrawler


class VideoInfo(BiliCrawler):
    '''
    视频信息爬取类
    '''
    def __init__(self):
        super().__init__()

    def get_video_info(self, bvid:str=None, aid:int=None) -> Optional[dict]:
        '''
        获取视频的详细信息
        
        :param 
            bvid: str: 视频的BV号
        :param 
            aid: int: 视频的AV号
        :return: 
            dict | None: 视频信息
        '''
        # 设置参数有bv号或者av号
        params = {}
        if bvid:
            params['bvid'] = bvid
        elif aid:
            params['aid'] = aid
        else:
            print("请提供bvid或者aid")
            return None

        resp = self._request(BiliAPI.VIDEO_INFO, params=params)

        # 如果resp返回的code不是0, 请求就是失败的
        if resp.get('code') != 0:
            # 输出错误信息
            print(f"获取视频信息失败: {resp.get('message')}")
            return None
        
        # 获取数据
        data = resp['data']

        video_info = {
            'bvid': data.get('bvid'),
            'aid': data.get('aid'),
            'title': data.get('title'),
            'desc': data.get('desc', ''),
            'duration': data.get('duration', 0),  # 秒
            'duration_str': self.format_duration(data.get('duration', 0)),
            'pubdate': data.get('pubdate'),
            'ctime': data.get('ctime'),
            'owner': {
                'mid': data.get('owner', {}).get('mid'),
                'name': data.get('owner', {}).get('name'),
                'face': data.get('owner', {}).get('face'),
            },
            'stat': {
                'view': data.get('stat', {}).get('view', 0),  # 播放
                'danmaku': data.get('stat', {}).get('danmaku', 0),  # 弹幕
                'reply': data.get('stat', {}).get('reply', 0),  # 评论
                'favorite': data.get('stat', {}).get('favorite', 0),  # 收藏
                'coin': data.get('stat', {}).get('coin', 0),  # 投币
                'share': data.get('stat', {}).get('share', 0),  # 分享
                'like': data.get('stat', {}).get('like', 0),  # 点赞
            },
            'pic': data.get('pic'),  # 封面
            'tname': data.get('tname'),  # 分区名
        }

        return video_info
    
    def get_video_tags(self, bvid:str=None, aid:int=None) -> list:
        """
        获取视频标签
        Args:
            bvid: 视频BV号
            aid: 视频AV号
        Returns:
            list: 标签列表
        """
        params = {}
        # 如果有bv号就用bv号
        # 没有bv号就用av号
        if bvid:
            params['bvid'] = bvid
        elif aid:
            params['aid'] = aid
        else:
            return []
        
        # 请求一下视频的tags
        resp = self._request(BiliAPI.VIDEO_TAGS, params=params)

        # code为0才有效
        if resp.get('code') != 0:
            return []

        tags = []
        for tag in resp.get('data', []):
            tags.append({
                'tag_id': tag.get('tag_id'),
                'tag_name': tag.get('tag_name')
            })
        
        return tags
    
    def get_video_comments(self, bvid:str=None, aid:int=None, sort:int=1, count:int=10) -> list:
        """
        获取视频热门评论
        Args:
            bvid: 视频BV号
            aid: 视频AV号
            sort: 排序方式 0=时间 1=点赞数(热度) 2=回复数
            count: 获取数量
        Returns:
            list: 评论列表
        """
        # 如果只有bvid需要先获取aid
        original_bvid = bvid
        if bvid and not aid:
            video_info = self.get_video_info(bvid=bvid)
            if video_info:
                aid = video_info['aid']
            else:
                return []
            
        params = {
            'type': 1,  # 1=视频 17=动态
            'oid': aid,
            'mode': sort + 1,  # 1=最新 2=按热度 3=按回复数
            'ps': min(count, 20),  # 每页最多20条
            'pn': 1,
        }

        # 使用专门的评论请求方法，带重试和反爬处理
        resp = self._request_reply(BiliAPI.REPLY_MAIN, params=params, bvid=original_bvid)

        if resp.get('code') != 0:
            print(f"获取评论失败: {resp.get('message')}")
            return []
        
        comments = []
        replies = resp.get('data', {}).get('replies', []) or []

        for reply in replies[:count]:
            comments.append({
                'rpid': reply.get('rpid'),
                'content': reply.get('content', {}).get('message', ''),
                'member': {
                    'mid': reply.get('member', {}).get('mid'),
                    'uname': reply.get('member', {}).get('uname'),
                },
                'like': reply.get('like', 0),
                'rcount': reply.get('rcount', 0),  # 回复数
                'ctime': reply.get('ctime'),
            })
        
        return comments
    
    def get_full_video_details(self, bvid:str=None, aid:str=None,
                               include_comments:bool=True, comment_count:int=10) -> Optional[dict]:
        """
        获取视频完整详情（包含基本信息、标签、评论）
        Args:
            bvid: 视频BV号
            aid: 视频AV号
            include_comments: 是否包含评论
            comment_count: 评论数量
        Returns:
            dict: 完整视频信息
        """
        # 获取基本信息
        video_info = self.get_video_info(bvid=bvid, aid=aid)
        if not video_info:
            return None
        
        # 获取tags
        tags = self.get_video_tags(bvid=video_info['bvid'])
        video_info['tags'] = tags

        # 获取热门评论
        if include_comments:
            comments = self.get_video_comments(
                aid = video_info['aid'],
                sort=1,
                count=comment_count
            )
            video_info['top_comments'] = comments
        
        return video_info
    
if __name__ == '__main__':
    video = VideoInfo()

    # 测试获取视频信息
    info = video.get_full_video_details(bvid='BV1mnvxBqEvj')
    if info:
        print(f"标题: {info['title']}")
        print(f"时长: {info['duration_str']}")
        print(f"播放: {info['stat']['view']}")
        print(f"点赞: {info['stat']['like']}")
        print(f"投币: {info['stat']['coin']}")
        print(f"收藏: {info['stat']['favorite']}")
        print(f"标签: {[t['tag_name'] for t in info['tags']]}")
        print(f"评论数: {len(info.get('top_comments', []))}")