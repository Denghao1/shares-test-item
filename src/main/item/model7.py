# Re-execute the finalized code after environment reset

import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from tabulate import tabulate
import warnings
from colorama import Fore, Style, init

init(autoreset=True)
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

def format_percent(value, is_rate=False):
    try:
        val = float(value) * 100
        val_str = f"{val:.2f}%"
        if is_rate:
            if val >= 50:
                return f"{Fore.GREEN}{val_str}✔{Style.RESET_ALL}"
            else:
                return f"{Fore.RED}{val_str}✖{Style.RESET_ALL}"
        else:
            if val > 0:
                return f"{Fore.GREEN}{val_str}▲{Style.RESET_ALL}"
            elif val < 0:
                return f"{Fore.RED}{val_str}▼{Style.RESET_ALL}"
            else:
                return val_str
    except:
        return "NaN"

def format_sign(value, is_rate=False):
    try:
        val = float(value) * 100
        val_str = f"{val:.2f}%"
        if is_rate:
            return f"{val_str}✔" if val >= 50 else f"{val_str}✖"
        else:
            return f"{val_str}▲" if val > 0 else f"{val_str}▼" if val < 0 else val_str
    except:
        return "NaN"

def run_fanbao_drop5to10_prev_zt_model(file_path, start_date_filter, end_date_filter):
    all_data = []
    for file in tqdm([f for f in os.listdir(file_path) if f.endswith('.csv')], desc="读取文件"):
        try:
            code = os.path.splitext(file)[0][:6]
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
            df['涨停连板数'] = 0

            for i in range(1, len(df)):
                if df.at[i, '是否涨停']:
                    df.at[i, '涨停连板数'] = df.at[i - 1, '涨停连板数'] + 1 if df.at[i - 1, '是否涨停'] else 1

            for i in range(2, len(df) - 3):
                if not df.at[i - 2, '是否涨停']:
                    continue
                if not (-0.10 <= df.at[i - 1, '涨幅'] <= -0.05):
                    continue

                today_high, today_pre_close, today_close = df.at[i, '最高'], df.at[i, '前收'], df.at[i, '收盘']
                if pd.isna(today_high) or pd.isna(today_pre_close) or pd.isna(today_close):
                    continue

                limit_price = round(today_pre_close * 1.095, 2)
                if not (round(today_close, 2) >= limit_price or round(today_high, 2) >= limit_price):
                    continue

                连板数 = int(df.at[i - 2, '涨停连板数'])
                record = {
                    '股票代码': code,
                    '日期': df.at[i - 1, '日期'],
                    '板数': f"{连板数}板" if 1 <= 连板数 <= 5 else "其他",
                }

                buy_price = today_high
                if i + 1 < len(df):
                    open2, close2 = df.at[i + 1, '开盘'], df.at[i + 1, '收盘']
                    record['第2天开盘收益'] = (open2 / buy_price - 1) if pd.notna(open2) and buy_price else np.nan
                    record['第2天尾盘收益'] = (close2 / buy_price - 1) if pd.notna(close2) and buy_price else np.nan
                if i + 2 < len(df):
                    open3, close3 = df.at[i + 2, '开盘'], df.at[i + 2, '收盘']
                    record['第3天开盘收益'] = (open3 / buy_price - 1) if pd.notna(open3) and buy_price else np.nan
                    record['第3天尾盘收益'] = (close3 / buy_price - 1) if pd.notna(close3) and buy_price else np.nan

                all_data.append(record)
        except Exception as e:
            print(f"读取文件 {file} 出错：{e}")

    df_all = pd.DataFrame(all_data)
    df_all = df_all[(df_all['日期'] >= start_date_filter) & (df_all['日期'] <= end_date_filter)]
    if df_all.empty:
        print("❌ 没有符合条件的数据")
        return

    def calc_stats(df, col):
        avg = df[col].mean()
        win_rate = (df[col] > 0).mean()
        return pd.DataFrame({
            f"{col}平均收益": [avg],
            f"{col}胜率": [win_rate]
        })

    grouped = df_all.groupby('板数').apply(lambda g: pd.concat([
        calc_stats(g, '第2天开盘收益'),
        calc_stats(g, '第2天尾盘收益'),
        calc_stats(g, '第3天开盘收益'),
        calc_stats(g, '第3天尾盘收益'),
    ], axis=1))

    counts = df_all['板数'].value_counts().to_dict()
    grouped.reset_index(level=1, drop=True, inplace=True)
    grouped.index = [f"{idx} ({counts.get(idx, 0)}条)" for idx in grouped.index]

    expected_cols = [
        '第2天开盘收益平均收益', '第2天开盘收益胜率',
        '第2天尾盘收益平均收益', '第2天尾盘收益胜率',
        '第3天开盘收益平均收益', '第3天开盘收益胜率',
        '第3天尾盘收益平均收益', '第3天尾盘收益胜率',
    ]
    grouped = grouped[[col for col in expected_cols if col in grouped.columns]]

    print("\n📊 前一天跌5-10%，两天前涨停，当天涨停买入，次日/次次日开收盘收益情况（按前两日连板数分类）")

    def format_color_all(x, col_name):
        return format_percent(x, is_rate='胜率' in col_name)

    def format_sign_all(x, col_name):
        return format_sign(x, is_rate='胜率' in col_name)

    grouped_fmt = grouped.copy()
    for col in grouped_fmt.columns:
        grouped_fmt[col] = grouped_fmt[col].apply(lambda x: format_color_all(x, col))
    grouped_print = grouped.copy()
    for col in grouped_print.columns:
        grouped_print[col] = grouped_print[col].apply(lambda x: format_sign_all(x, col))

    print(tabulate(grouped_fmt, headers='keys', tablefmt='psql', stralign='center'))

    sample_size = min(10, len(df_all))
    print("\n🔍 随机抽取10条原始记录供验证：")
    sample_df = df_all.sample(n=sample_size, random_state=42)
    for col in ['第2天开盘收益', '第2天尾盘收益', '第3天开盘收益', '第3天尾盘收益']:
        sample_df[col] = sample_df[col].apply(lambda x: f"{x * 100:.2f}%" if pd.notna(x) else "NaN")
    print(tabulate(sample_df[['股票代码', '日期', '板数',
                              '第2天开盘收益', '第2天尾盘收益',
                              '第3天开盘收益', '第3天尾盘收益']], headers='keys', tablefmt='psql', stralign='center'))

    return grouped_print
