# 炸板策略回测结果1
# item/model1.py
#

import pandas as pd
import numpy as np
import os
import pickle
from tqdm import tqdm

def run_model1(file_path, cache_path, start_date_filter, end_date_filter):
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            df_all = pickle.load(f)
    else:
        all_stock = []
        for file in tqdm([f for f in os.listdir(file_path) if f.endswith('.csv')], desc="读取文件"):
            try:
                df = pd.read_csv(os.path.join(file_path, file), encoding='gbk', parse_dates=['交易日期'])
                df.sort_values('交易日期', inplace=True)
                df['前收'] = df['收盘价_复权'].shift(1)
                df['涨跌幅'] = df['收盘价_复权'] / df['前收'] - 1
                df['最高涨幅'] = df['最高价_复权'] / df['前收'] - 1
                df['是否炸板'] = (df['最高涨幅'] >= 0.099) & (df['涨跌幅'] < 0.099) & (df['最高涨幅'] <= 0.105)
                for idx in df[df['是否炸板']].index:
                    record = {'交易日期': df.at[idx, '交易日期']}
                    for i in range(5):
                        if idx + i + 1 >= len(df):
                            break
                        day = f'第{i+1}日'
                        open_price = df.at[idx + i + 1, '开盘价_复权']
                        close_price = df.at[idx + i + 1, '收盘价_复权']
                        pre_close = df.at[idx + i, '收盘价_复权']
                        record[f'{day}涨幅'] = (close_price / pre_close - 1) if pd.notna(pre_close) else np.nan
                        record[f'{day}收益'] = (close_price / open_price - 1) if pd.notna(open_price) else np.nan
                    all_stock.append(record)
            except Exception as e:
                print(f"读取文件 {file} 出错：{e}")
        df_all = pd.DataFrame(all_stock)
        with open(cache_path, 'wb') as f:
            pickle.dump(df_all, f)

    df_all = df_all[(df_all['交易日期'] >= start_date_filter) & (df_all['交易日期'] <= end_date_filter)]
    if df_all.empty:
        return "❌ 无有效炸板数据，请检查数据时间范围或数据格式。"

    result = pd.DataFrame()
    for i in range(1, 6):
        result.loc[f'第{i}日', '平均涨幅'] = df_all[f'第{i}日涨幅'].mean()
        result.loc[f'第{i}日', '平均收益'] = df_all[f'第{i}日收益'].mean()
    return result.fillna(0).to_string(float_format="{:.2%}".format)
