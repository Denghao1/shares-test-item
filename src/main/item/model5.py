# 不同连板涨停买入策略回测结果

import os
import pandas as pd
import numpy as np
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

def safe_read_csv(filepath):
    encodings_to_try = ['utf-8', 'gbk', 'utf-8-sig', 'ISO-8859-1']
    for enc in encodings_to_try:
        try:
            return pd.read_csv(filepath, encoding=enc, parse_dates=['日期'])
        except Exception:
            continue
    print(f"❌ 文件无法读取：{filepath}")
    return None

def run_lianban_buy_model(file_path, start_date_filter, end_date_filter):
    all_data = []

    for file in tqdm([f for f in os.listdir(file_path) if f.endswith('.csv')], desc="读取文件"):
        try:
            code = os.path.splitext(file)[0][:6]
            # ✅ 排除不可交易股票（非主板，如创业板、科创板、北交所）
            if not code.isdigit() or len(code) != 6:
                continue
            if not (code.startswith('00') or code.startswith('60')):
                continue

            df = safe_read_csv(os.path.join(file_path, file))
            if df is None or df.empty:
                continue

            df.sort_values('日期', inplace=True)
            df.reset_index(drop=True, inplace=True)

            df['前收'] = df['收盘'].shift(1)
            df['涨幅'] = df['收盘'] / df['前收'] - 1
            df['是否涨停'] = (df['涨幅'] >= 0.095) & (df['涨幅'] <= 0.105)

            连板计数 = 0
            for i in range(1, len(df) - 3):
                if df.at[i, '是否涨停']:
                    连板计数 += 1
                else:
                    连板计数 = 0

                if 1 <= 连板计数 <= 5:
                    record = {
                        '股票代码': code,
                        '日期': df.at[i, '日期'],
                        '买入板数': 连板计数
                    }

                    # 第2天（i+1）
                    if i + 1 < len(df):
                        open2 = df.at[i + 1, '开盘']
                        close2 = df.at[i + 1, '收盘']
                        record['第2天尾盘卖出'] = (close2 / open2 - 1) if open2 else np.nan

                    # 第3天（i+2）
                    if i + 2 < len(df):
                        open3 = df.at[i + 2, '开盘']
                        close3 = df.at[i + 2, '收盘']
                        record['第3天开盘卖出'] = (open3 / close2 - 1) if close2 else np.nan
                        record['第3天尾盘卖出'] = (close3 / close2 - 1) if close2 else np.nan

                    all_data.append(record)

        except Exception as e:
            print(f"读取文件 {file} 出错：{e}")

    df_all = pd.DataFrame(all_data)
    df_all = df_all[(df_all['日期'] >= start_date_filter) & (df_all['日期'] <= end_date_filter)]

    if df_all.empty:
        print("❌ 没有符合连板买入条件的数据")
        return

    result = pd.DataFrame()
    for b in range(1, 6):
        temp = df_all[df_all['买入板数'] == b]
        if not temp.empty:
            result.loc[f"{b}板买入", '第2天尾盘卖出'] = temp['第2天尾盘卖出'].mean()
            result.loc[f"{b}板买入", '第3天开盘卖出'] = temp['第3天开盘卖出'].mean()
            result.loc[f"{b}板买入", '第3天尾盘卖出'] = temp['第3天尾盘卖出'].mean()

    print("\n📊 连板买入策略回测结果：")
    print(result.fillna(0).to_string(float_format="{:.2%}".format))

    return result
