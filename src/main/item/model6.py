import os
import pandas as pd
import numpy as np
from tqdm import tqdm
import warnings
from tabulate import tabulate

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

def run_zhuangting_fanbao_model(file_path, start_date_filter, end_date_filter):
    all_data = []

    for file in tqdm([f for f in os.listdir(file_path) if f.endswith('.csv')], desc="读取文件"):
        try:
            code = os.path.splitext(file)[0][:6]
            if not code.isdigit() or len(code) != 6:
                continue
            if not (code.startswith('00') or code.startswith('60')):
                continue  # 排除非主板

            df = safe_read_csv(os.path.join(file_path, file))
            if df is None or df.empty:
                continue

            df.sort_values('日期', inplace=True)
            df.reset_index(drop=True, inplace=True)

            df['前收'] = df['收盘'].shift(1)
            df['涨幅'] = df['收盘'] / df['前收'] - 1
            df['是否涨停'] = (df['涨幅'] >= 0.095) & (df['涨幅'] <= 0.105)

            for i in range(2, len(df) - 3):
                if not df.at[i - 2, '是否涨停']:
                    continue  # 第1日未涨停，跳过

                if df.at[i - 1, '是否涨停']:
                    continue  # 第2日又涨停，跳过

                prev_close = df.at[i - 1, '收盘']
                today_high = df.at[i, '最高']
                today_pre_close = df.at[i, '前收']
                today_close = df.at[i, '收盘']
                if pd.isna(prev_close) or pd.isna(today_high) or pd.isna(today_pre_close) or pd.isna(today_close):
                    continue

                limit_price = round(today_pre_close * 1.095, 2)
                是否涨停_or_炸板 = (round(today_close, 2) >= limit_price) or (round(today_high, 2) >= limit_price)
                if not 是否涨停_or_炸板:
                    continue

                涨幅值 = df.at[i - 1, '涨幅']
                涨幅区间起 = int((涨幅值 // 0.02) * 2)
                区间标签 = f"{涨幅区间起}%–{涨幅区间起 + 2}%"

                record = {
                    '股票代码': code,
                    '日期': df.at[i - 1, '日期'],
                    '第2日收盘涨幅': 涨幅值,
                    '涨幅区间': 区间标签,
                    'sort_key': 涨幅区间起
                }

                if i + 1 < len(df):
                    open4 = df.at[i + 1, '开盘']
                    close4 = df.at[i + 1, '收盘']
                    buy_price = today_high
                    record['第4天开盘收益'] = (open4 / buy_price - 1) if pd.notna(open4) and buy_price != 0 else np.nan
                    record['第4天尾盘收益'] = (close4 / buy_price - 1) if pd.notna(close4) and buy_price != 0 else np.nan

                if i + 2 < len(df):
                    open5 = df.at[i + 2, '开盘']
                    close5 = df.at[i + 2, '收盘']
                    buy_price = today_high
                    record['第5天开盘收益'] = (open5 / buy_price - 1) if pd.notna(open5) and buy_price != 0 else np.nan
                    record['第5天尾盘收益'] = (close5 / buy_price - 1) if pd.notna(close5) and buy_price != 0 else np.nan

                all_data.append(record)

        except Exception as e:
            print(f"读取文件 {file} 出错：{e}")

    df_all = pd.DataFrame(all_data)
    df_all = df_all[(df_all['日期'] >= start_date_filter) & (df_all['日期'] <= end_date_filter)]

    if df_all.empty:
        print("❌ 没有符合炸板回测条件的数据")
        return

    grouped = df_all.groupby(['涨幅区间', 'sort_key'])[['第4天开盘收益','第4天尾盘收益', '第5天开盘收益', '第5天尾盘收益']].mean().reset_index()
    grouped = grouped.sort_values(by='sort_key').drop(columns='sort_key').set_index('涨幅区间')

    grouped = grouped.fillna(0)
    grouped = grouped.applymap(lambda x: f"{x * 100:.2f}%")

    print("\n📊 炸板次日涨停买入后，不同第2天涨幅区间下的收益率：")
    print(tabulate(grouped, headers='keys', tablefmt='psql', stralign='center'))

    sample_size = 10
    if len(df_all) < sample_size:
        sample_size = len(df_all)

    print("\n🔍 随机抽取10条原始记录供验证：")
    sample_df = df_all.sample(n=sample_size, random_state=42)

    def format_pct(x):
        return f"{x * 100:.2f}%" if pd.notna(x) else "NaN"

    sample_df_print = sample_df.copy()
    sample_df_print['第2日收盘涨幅'] = sample_df_print['第2日收盘涨幅'].apply(format_pct)
    sample_df_print['第4天开盘收益'] = sample_df_print['第4天开盘收益'].apply(format_pct)
    sample_df_print['第4天尾盘收益'] = sample_df_print['第4天尾盘收益'].apply(format_pct)
    sample_df_print['第5天开盘收益'] = sample_df_print['第5天开盘收益'].apply(format_pct)
    sample_df_print['第5天尾盘收益'] = sample_df_print['第5天尾盘收益'].apply(format_pct)
    data_str = sample_df_print[['股票代码', '日期', '第2日收盘涨幅', '涨幅区间',
                           '第4天开盘收益', '第4天尾盘收益', '第5天开盘收益', '第5天尾盘收益']]
    print(tabulate(data_str, headers='keys', tablefmt='psql', stralign='center'))

    return grouped
