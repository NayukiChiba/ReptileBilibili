'''
获取user的基本信息
'''

import os
import json
from typing import Optional
from utils import format_number
from crawler import BiliCrawler
from config import BiliAPI, DATA_DIR


class UserInfo(BiliCrawler):
    '''
    用户信息爬取类
    '''

    def __init__(self):
        super().__init__()
        self.data_file = os.path.join(DATA_DIR, 'user_info.json')
    
    def get_nav_info(self) -> Optional[dict]:
        '''
        获取当前user的导航信息
    
        :return: dict: 用户导航信息
        '''
        resp = self._request(BiliAPI.NAV_INFO)

        if resp.get('code') != 0 or not resp.get('data', {}).get('isLogin'):
            print("未登录或获取信息失败")
            return None
        
        return resp['data']
    
    def get_user_info(self, mid: int = None) -> Optional[dict]:
        '''
        获取用户空间的详细信息
        
        :param mid: 用户的mid, 如果是None就表示获取当前登录用户信息
        
        :return: dict: 用户信息
        '''

        if mid is None:
            mid = self.get_mid()
            if not mid:
                print("未登录")
                return None
        
        params = {'mid': mid}
        resp = self._request_wbi(BiliAPI.USER_INFO, params=params)

        if resp.get('code') != 0:
            print(f"获取用户信息失败: {resp.get('message')}")
            return None
    
        data = resp['data']

        user_info = {
            'mid': data.get('mid'),
            'name': data.get('name'),
            'sex': data.get('sex'),
            'face': data.get('face'),  # 头像
            'sign': data.get('sign'),  # 签名
            'level': data.get('level'),  # 等级
            'silence': data.get('silence'),  # 是否被封禁
            'vip': {
                'type': data.get('vip', {}).get('type'),  # 0=无 1=月度 2=年度
                'status': data.get('vip', {}).get('status'),  # 0=无 1=有
                'label': data.get('vip', {}).get('label', {}).get('text', ''),
            },
            'official': {
                'role': data.get('official', {}).get('role'),
                'title': data.get('official', {}).get('title'),
            },
            'birthday': data.get('birthday'),
            'school': data.get('school', {}).get('name', '') if data.get('school') else '',
            'profession': data.get('profession', {}).get('name', '') if data.get('profession') else '',
        }

        return user_info

    def get_user_stat(self, mid: int = None) -> Optional[dict]:
        '''
        获取用户关系状态统计(关注数、粉丝数等)
        
        :param mid: 用户MID
        :type mid: int
        :return: dict: 统计信息
        '''
        # 如果mid不存在就获取mid
        if mid is None:
            mid = self.get_mid()
        
        params = {'vmid': mid}
        resp = self._request(BiliAPI.USER_STAT, params=params)

        if resp.get('code') != 0:
            print(f"获取用户统计失败: {resp.get('message')}")
            return None
        
        data = resp['data']
        user_stat = {
            'mid': data.get('mid'),
            'following': data.get('following', 0),  # 关注数
            'whisper': data.get('whisper', 0),  # 悄悄关注
            'black': data.get('black', 0),  # 黑名单
            'follower': data.get('follower', 0),  # 粉丝数
        }

        return user_stat
    
    def get_up_stat(self, mid: int = None) -> Optional[dict]:
        '''
        获取Up主的状态数
        
        :param mid: 用户MID
        :return: UP主统计
        '''
        if mid is None:
            mid = self.get_mid()

        params = {'mid': mid}
        resp = self._request_wbi(BiliAPI.USER_UPSTAT, params=params)

        if resp.get('code') != 0:
            return None
        
        data = resp['data']

        up_stat = {
            'archive_view': data.get('archive', {}).get('view', 0),  # 视频播放数
            'article_view': data.get('article', {}).get('view', 0),  # 文章阅读数
            'likes': data.get('likes', 0),  # 获赞数
        }

        return up_stat
    
    def get_full_user_info(self, mid: int=None) -> Optional[dict]:
        '''
        获取用户的完整信息(包含基本信息、统计等)
        
        :param mid: 用户的MID
        :return: 完整用户信息
        '''
        if mid is None:
            mid = self.get_mid()

        # 获取基本信息
        user_info = self.get_user_info(mid=mid)
        if not user_info:
            return None
        
        # 获取关系统计
        stat = self.get_user_stat(mid=mid)
        if stat:
            user_info['stat'] = stat

        # 获取up主统计
        up_stat = self.get_up_stat(mid=mid)
        if up_stat:
            user_info['up_stat'] = up_stat

        return user_info
    
    def save_user_info(self, user_info: dict = None) -> bool:
        '''
        保存用户信息到文件
        
        :param user_info: 用户信息, 不传入就自动获取

        :return: 是否成功
        '''
        if user_info is None:
            user_info = self.get_full_user_info()

        if not user_info:
            return False

        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(user_info, f, ensure_ascii=False, indent=2)
        
        print(f"用户信息已保存到: {self.data_file}")
        return True
    
    def print_user_info(self, user_info: dict = None):
        '''
        打印用户信息
        
        :param user_info: 用户信息
        '''
        if user_info is None:
            user_info = self.get_full_user_info()
        
        if not user_info:
            return
        
        print("\n" + "=" * 50)
        print("用户基本信息")
        print("=" * 50)
        print(f"昵称: {user_info.get('name')}")
        print(f"UID: {user_info.get('mid')}")
        print(f"性别: {user_info.get('sex')}")
        print(f"等级: LV{user_info.get('level')}")
        print(f"签名: {user_info.get('sign', '')[:50]}...")

        if user_info.get('vip', {}).get('status'):
            print(f"会员: {user_info['vip'].get('label', '大会员')}")
        
        if user_info.get('official', {}).get('title'):
            print(f"认证:{user_info['official']['title']}")

        if user_info.get('stat'):
            print("\n" + '-' * 30)
            print("关系统计: \n")
            print(f"    关注: {format_number(user_info['stat'].get('following', 0))}")
            print(f"    粉丝: {format_number(user_info['stat'].get('follower', 0))}")

        if user_info.get('up_stat'):
            print("\n" + "-" * 30)
            print("  UP主统计:")
            print(f"    播放量: {format_number(user_info['up_stat'].get('archive_view', 0))}")
            print(f"    阅读量: {format_number(user_info['up_stat'].get('article_view', 0))}")
            print(f"    获赞数: {format_number(user_info['up_stat'].get('likes', 0))}")
        
        print("=" * 50)


if __name__ == "__main__":
    user = UserInfo()

    # 获取并打印当前登录用户信息
    info = user.get_full_user_info()
    if info:
        user.print_user_info(info)
        user.save_user_info(info)