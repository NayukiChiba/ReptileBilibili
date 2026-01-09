'''
扫码登录板块
'''

import requests
import time
import qrcode
from io import BytesIO
from config import HEADERS, BiliAPI, save_cookies, load_cookies


class BiliLogin:
    '''
    扫码登录类
    '''

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.qrcode_key = None
        self.cookies = {}

    def generate_qrcode(self) -> str:
        '''
        :returns: str: 二维码的url
        '''
        response = self.session.get(BiliAPI.QR_GENERATE)
        
        # 检查HTTP状态码
        if response.status_code != 200:
            print(f'HTTP请求失败, 状态码: {response.status_code}')
            print(f'响应内容: {response.text[:500]}')
            raise Exception(f'HTTP请求失败: {response.status_code}')
        
        # 检查响应内容是否为空
        if not response.text or not response.text.strip():
            print(f'服务器返回空响应')
            print(f'响应头: {dict(response.headers)}')
            raise Exception('服务器返回空响应')
        
        # 获取数据的json形式
        try:
            data = response.json()
        except Exception as e:
            print(f'JSON解析失败: {e}')
            print(f'响应状态码: {response.status_code}')
            print(f'响应内容前500字符: {response.text[:500]}')
            raise

        if data['code'] != 0:
            raise Exception(f"获取二维码失败: {data['message']}")
        
        self.qrcode_key = data['data']['qrcode_key']
        qr_url = data['data']['url']

        return qr_url

    def show_qrcode_terminal(self, url: str):
        '''
        在终端中显示二维码
        
        :param url: 二维码的内容url
        '''

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # 在终端打印二维码
        qr.print_ascii(invert=True)
    
    def save_qrcode_image(self, url:str, filename:str='qrcode.png'):
        '''
        保存二维码图片到文件中
        :param url: 二维码的url
        :param filename: 保存的文件名字
        '''
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color='black', back_color='white')
        img.save(filename)
        print(f'二维码已保存在: {filename}')

    def poll_login_status(self) -> dict:
        '''
        轮询登录状态
        
        :return: 登录状态信息
        '''
        params = {
            'qrcode_key': self.qrcode_key,
        }
        response = self.session.get(BiliAPI.QR_POLL, params=params)
        data = response.json()

        # 更新cookies
        self.cookies.update(requests.utils.dict_from_cookiejar(response.cookies))

        return data
    

    def _parse_url_cookies(self, url: str):
        '''
        从登录成功的url中解析cookies参数
        
        :param url: 登录成功返回的url
        '''
        if '?' not in url:
            return
        
        query_string = url.split('?')[1]
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                self.cookies[key] = value


    def login(self, show_in_terminal: bool = True) -> bool:
        '''
        扫码登录主流程
        
        :param show_in_terminal: 是否在终端显示二维码
        :return: 是否登录成功
        '''

        print('=' * 50)
        print('Bilibili扫码登录')
        print('=' * 50)

        # 生成二维码
        print('\n 正在获取二维码...')
        qr_url = self.generate_qrcode()

        # 显示二维码
        if show_in_terminal:
            print('\n 请使用B站APP扫描下方二维码: \n')
            self.show_qrcode_terminal(qr_url)
        else:
            self.save_qrcode_image(qr_url)
            print('\n请使用B站APP扫描二维码文件登录')

        print('\n等待扫码')        

        # 轮询登录状态
        while True:
            result = self.poll_login_status()
            code = result['data']['code']

            if code == 0:
                # 登录成功
                print('\n登录成功!')

                # 从url中提取额外的cookies
                url = result['data']['url']
                self._parse_url_cookies(url)

                # 保存cookies
                save_cookies(self.cookies)
                print('\ncookies已保存')

                return True

            elif code == 86101:
                # 未扫码
                pass

            elif code == 86090:
                # 已扫码, 等待确认
                print('\r已扫码, 请在手机上确认登录...', end='', flush=True)

            elif code == 86038:
                # 二维码已过期
                print('\n二维码已过期, 请重新登录')
                return False
            
            elif code == 86083:
                # 扫码被拒绝
                print('\n 登录已被取消')
                return False

            else:
                print('\n未知状态码:{code}')
            
            time.sleep(1)

    def check_login_status(self) -> dict :
        '''
        检查当前登录的状态
        
        :return: 用户信息, 如果未登录就返回None
        '''
        cookies = load_cookies()
        if not cookies:
            return None
        
        response = self.session.get(BiliAPI.NAV_INFO, cookies=cookies)
        data = response.json()

        if data['code'] == 0 and data['data']['isLogin']:
            return data['data']
        return None
    
def login():
    '''
    login主函数
    '''
    bililogin = BiliLogin()

    # 先检查是否已经登录
    print('检查登录状态...')
    user_info = bililogin.check_login_status()

    if user_info:
        print(f'\n已登录账号: {user_info['uname']}')
        print(f'UID: {user_info['mid']}')
        print(f'等级: LV{user_info['level_info']['current_level']}')

        choice = input('\n是否重新登录?(y/N): ').strip().lower()

        if choice != 'y':
            return True
        
    return bililogin.login()

if __name__ == '__main__':
    login()