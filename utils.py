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