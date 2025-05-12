cookie = input('输入你的cookie:')
cookie_lst = cookie.split(';')
cookie_dict = {}
for cookie_item in cookie_lst:
    cookie_item_name = cookie_item.split("=")[0].strip()
    cookie_item_value = cookie_item.split('=')[1].strip()
    cookie_dict[cookie_item_name] = cookie_item_value

COOKIES = cookie_dict
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}
MID = COOKIES['DedeUserID']
URL_HISTORY = 'https://api.bilibili.com/x/web-interface/history/cursor?view_at=0&business='

