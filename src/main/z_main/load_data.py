# 获取数据和设置时间区间
#
#
import os
import pandas as pd

# 获取数据文件路径
file_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..','..', 'mainData', 'data_2025')
)

# 缓存路径
cache_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..','..','mainData', 'cached_stock_data.pkl')
)

# 起止时间
start_date_filter = pd.to_datetime('2018-12-01')
end_date_filter = pd.to_datetime('2025-06-30')

__all__ = ['file_path', 'cache_path', 'start_date_filter', 'end_date_filter']
