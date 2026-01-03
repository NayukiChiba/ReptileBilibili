
import csv
import os

def format_number(num: int) -> str:
    '''
    格式化数字显示(10000 -> 1万)
    
    :param num: 数字
    :return: str: 格式化之后的数字
    '''
    if num >= 100000000:
        return f'{num / 100000000:.1f}亿'
    elif num >= 10000:
        return f'{num / 10000:.1f}万'
    return str(num)


def timestamp_to_datetime(timestamp:int) -> str:
    """
    时间戳转换为日期时间字符串
    Args:
        timestamp: Unix时间戳
    Returns:
        str: 格式化的日期时间字符串
    """
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def write_head(file: str, heads: list):
    """
    写入CSV文件表头(如果文件不存在)
    Args:
        file: CSV文件路径
        heads: 表头列表
    """
    # 确保目录存在
    dir_path = os.path.dirname(file)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    # 如果文件已存在则跳过
    if os.path.exists(file):
        return
    
    with open(file, mode='w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(heads)


def write2csv(file: str, row: list):
    """
    向CSV文件追加一行数据
    Args:
        file: CSV文件路径
        row: 要写入的行数据
    """
    # 确保目录存在
    dir_path = os.path.dirname(file)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with open(file, mode='a', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(row)