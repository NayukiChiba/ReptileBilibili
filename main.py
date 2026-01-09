# -*- coding: utf-8 -*-
"""
B站爬虫 - 主程序入口
使用requests实现的B站数据爬虫

功能列表:
1. 获取过去一周的观看历史
2. 获取关注的UP主及其视频
3. 获取所有收藏视频
4. 获取订阅的番剧
5. 获取最近点赞/投币的视频
6. 获取用户基本信息
"""

from login import login, BiliLogin
from user_info import UserInfo
from history_video import HistoryVideo
from follow_list import FollowList
from favorite_video import FavoriteVideo
from bangumi_list import BangumiList
from like_coin_video import LikeCoinVideo


def show_menu():
    """显示功能菜单"""
    print("\n" + "=" * 60)
    print("  功能菜单")
    print("=" * 60)
    print("  1. 获取用户基本信息")
    print("  2. 获取过去一周的观看历史")
    print("  3. 获取关注列表")
    print("  4. 获取关注UP主的视频(最新10个+热门10个)")
    print("  5. 获取所有收藏视频")
    print("  6. 获取订阅的番剧")
    print("  7. 获取最近点赞的视频(100个)")
    print("  8. 获取最近投币的视频(100个)")
    print("  9. 执行所有爬取任务")
    print("  0. 退出")
    print("-" * 60)


def crawl_user_info():
    """爬取用户基本信息"""
    print("\n[任务] 获取用户基本信息")
    print("-" * 40)
    
    user = UserInfo()
    info = user.get_full_user_info()
    if info:
        user.print_user_info(info)
        user.save_user_info(info)


def crawl_history(include_detail: bool = True):
    """爬取观看历史"""
    print("\n[任务] 获取过去一周的观看历史")
    print("-" * 40)
    
    history = HistoryVideo()
    records = history.get_week_history(include_detail=include_detail)
    history.save_history(records, include_detail=include_detail)


def crawl_follow_list():
    """爬取关注列表"""
    print("\n[任务] 获取关注列表")
    print("-" * 40)
    
    follow = FollowList()
    follows = follow.get_all_follows()
    follow.save_follow_list(follows)


def crawl_up_videos(recent_count: int = 10, popular_count: int = 10):
    """爬取关注UP主的视频"""
    print(f"\n[任务] 获取关注UP主的视频(最新{recent_count}个+热门{popular_count}个)")
    print("-" * 40)
    
    follow = FollowList()
    up_list = follow.get_all_up_info(
        recent_count=recent_count,
        popular_count=popular_count,
        include_detail=True
    )
    follow.save_all_up_videos(up_list)


def crawl_favorites(include_detail: bool = True):
    """爬取收藏视频"""
    print("\n[任务] 获取所有收藏视频")
    print("-" * 40)
    
    fav = FavoriteVideo()
    favorites = fav.get_all_favorites(include_detail=include_detail)
    fav.save_all_favorites(favorites, include_detail=include_detail)


def crawl_bangumi():
    """爬取订阅的番剧"""
    print("\n[任务] 获取订阅的番剧")
    print("-" * 40)
    
    bangumi = BangumiList()
    subs = bangumi.get_all_subscriptions()
    bangumi.print_bangumi_list(subs)
    bangumi.save_bangumi_list(subs)


def crawl_liked_videos(include_detail: bool = True):
    """爬取点赞视频"""
    print("\n[任务] 获取最近点赞的视频")
    print("-" * 40)
    
    lc = LikeCoinVideo()
    videos = lc.get_all_liked_videos(max_count=100)
    lc.save_liked_videos(videos, include_detail=include_detail)


def crawl_coined_videos(include_detail: bool = True):
    """爬取投币视频"""
    print("\n[任务] 获取最近投币的视频")
    print("-" * 40)
    
    lc = LikeCoinVideo()
    videos = lc.get_all_coined_videos(max_count=100)
    lc.save_coined_videos(videos, include_detail=include_detail)


def crawl_all(include_detail: bool = True):
    """执行所有爬取任务"""
    print("\n" + "=" * 60)
    print("  开始执行所有爬取任务")
    print("=" * 60)
    
    # 1. 用户信息
    crawl_user_info()
    
    # 2. 观看历史
    crawl_history(include_detail=include_detail)
    
    # 3. 关注列表
    crawl_follow_list()
    
    # 4. UP主视频 (这个任务可能很耗时，可以注释掉)
    print("\n[提示] UP主视频爬取可能耗时较长，如需跳过请在代码中注释")
    try:
        crawl_up_videos(recent_count=10, popular_count=10)
    except KeyboardInterrupt:
        print("\n已跳过UP主视频爬取")
    
    # 5. 收藏视频
    crawl_favorites(include_detail=include_detail)
    
    # 6. 番剧订阅
    crawl_bangumi()
    
    # 7. 点赞视频
    crawl_liked_videos(include_detail=include_detail)
    
    # 8. 投币视频
    crawl_coined_videos(include_detail=include_detail)
    
    print("\n" + "=" * 60)
    print("  所有爬取任务完成!")
    print("=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("  B站数据爬虫 - ReptileBilibili")
    print("  使用 requests 实现")
    print("=" * 60)
    
    # 1. 登录
    if not login():
        print("\n登录失败, 程序退出")
        return
    
    # 获取用户信息
    bili_login = BiliLogin()
    user_info = bili_login.check_login_status()
    
    if user_info:
        print("\n" + "=" * 60)
        print(f"  当前用户: {user_info['uname']}")
        print(f"  UID: {user_info['mid']}")
        print("=" * 60)
    
    # 功能菜单循环
    while True:
        show_menu()
        choice = input("请选择功能 (0-9): ").strip()
        
        try:
            if choice == '0':
                print("\n再见!")
                break
            elif choice == '1':
                crawl_user_info()
            elif choice == '2':
                crawl_history(include_detail=True)
            elif choice == '3':
                crawl_follow_list()
            elif choice == '4':
                crawl_up_videos()
            elif choice == '5':
                crawl_favorites(include_detail=True)
            elif choice == '6':
                crawl_bangumi()
            elif choice == '7':
                crawl_liked_videos(include_detail=True)
            elif choice == '8':
                crawl_coined_videos(include_detail=True)
            elif choice == '9':
                crawl_all(include_detail=True)
            else:
                print("无效选择，请重试")
        except KeyboardInterrupt:
            print("\n\n已中断当前任务")
        except Exception as e:
            print(f"\n任务出错: {e}")


if __name__ == '__main__':
    main()
