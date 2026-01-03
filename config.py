import json
import os

# 文件路径配置

## 配置保存位置
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
## COOKIE保存位置
COOKIE_FILE = os.path.join(CONFIG_DIR, 'cookies.json')
## 数据保存位置
DATA_DIR = os.path.join(CONFIG_DIR, 'data')

# 创建data文件夹, 确保data文件夹存在
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    'Origin': 'https://www.bilibili.com',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
}

# 评论 API 专用请求头（额外添加的）
REPLY_HEADERS = {
    'Referer': 'https://www.bilibili.com/video/',
}

# B站API地址
class BiliAPI:
    """B站API接口地址"""
    # 登录相关
    QR_GENERATE = 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate'  # 获取二维码
    QR_POLL = 'https://passport.bilibili.com/x/passport-login/web/qrcode/poll'  # 轮询登录状态
    NAV_INFO = 'https://api.bilibili.com/x/web-interface/nav'  # 获取用户导航信息
    
    # 用户信息相关
    USER_INFO = 'https://api.bilibili.com/x/space/wbi/acc/info'  # 用户空间详细信息
    USER_STAT = 'https://api.bilibili.com/x/relation/stat'  # 用户关系状态统计
    USER_UPSTAT = 'https://api.bilibili.com/x/space/upstat'  # UP主状态(播放/阅读)
    
    # 历史记录相关
    HISTORY = 'https://api.bilibili.com/x/web-interface/history/cursor'  # 观看历史
    
    # 关注相关
    FOLLOW = 'https://api.bilibili.com/x/relation/followings'  # 关注列表
    
    # 收藏夹相关
    FAVORITE_LIST = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all'  # 收藏夹列表
    FAVORITE_RESOURCE = 'https://api.bilibili.com/x/v3/fav/resource/list'  # 收藏夹内容
    
    # UP主视频相关
    SPACE_VIDEO = 'https://api.bilibili.com/x/space/wbi/arc/search'  # UP主视频列表
    
    # 视频信息相关
    VIDEO_INFO = 'https://api.bilibili.com/x/web-interface/view'  # 视频详情
    VIDEO_DETAIL = 'https://api.bilibili.com/x/web-interface/view/detail'  # 视频详情(含推荐/Tag等)
    VIDEO_TAGS = 'https://api.bilibili.com/x/tag/archive/tags'  # 视频标签
    VIDEO_DESC = 'https://api.bilibili.com/x/web-interface/archive/desc'  # 视频简介
    
    # 评论相关
    REPLY_MAIN = 'https://api.bilibili.com/x/v2/reply/main'  # 评论列表
    REPLY_REPLY = 'https://api.bilibili.com/x/v2/reply/reply'  # 评论回复
    
    # 番剧订阅相关
    BANGUMI_LIST = 'https://api.bilibili.com/x/space/bangumi/follow/list'  # 追番列表
    
    # 点赞/投币记录相关
    LIKE_VIDEO = 'https://api.bilibili.com/x/space/like/video'  # 点赞视频列表(仅最近)
    COIN_VIDEO = 'https://member.bilibili.com/x/web/coin/video'  # 投币视频列表


# 获取COOKIES
def load_cookies():
    '''
    从文件中加载COOKIE
    returns: 
        dict: Cookie字典, 如果文件不存在就返回空字典
    '''

    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f :
            return json.load(f)
    return {}

# 保存COOKIE到文件中
def save_cookies(cookies: dict):
    '''
    获取到了cookies, 把他保存在COOKIE_FILE
    args:
        dict: 获取到的cookie字典
    '''
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

# 获取用户的mid
def get_mid():
    '''
    从COOKIE中获取用户的MID
    returns:
        str: 用户的MID, 不存在就返回None
    '''
    cookies = load_cookies()
    return cookies.get('DedeUserID')
