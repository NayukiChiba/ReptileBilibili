# python文件
# 开发时间：2024/4/25 8:14
import up_list
import up_video
import favorite_video
import history_video
from config import MID

if __name__ == '__main__':
    up_list.GetUpList(MID).run()
    up_video.GetUpVideoInfo().run()
    favorite_video.GetFavoriteVideoInfo().run()
    history_video.GetHistoryVideo().run()
