# 断板次日买入回测结果

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

def simulate_from_df_random_trades(
    df_all: pd.DataFrame,
    start_date="2022-12-01",
    end_date="2025-06-30",
    num_trades=100,
    initial_fund=100000,
    seed=None
):
    """
    根据 df_all 中的“第2天尾盘收益”模拟资金增长：
    - 只使用日期在 start_date 到 end_date 范围内的数据
    - 随机抽取 num_trades 条交易记录
    - 每次用全部资金买入，收益根据“第2天尾盘收益”计算
    """
    if seed is not None:
        np.random.seed(seed)
    
    # 过滤日期范围
    df_filtered = df_all[(df_all['日期'] >= pd.to_datetime(start_date)) & (df_all['日期'] <= pd.to_datetime(end_date))]
    df_filtered = df_filtered.dropna(subset=['第2天尾盘收益'])
    if len(df_filtered) < num_trades:
        print(f"警告：符合日期和收益率条件的数据不足{num_trades}条，只能模拟{len(df_filtered)}次交易。")
        num_trades = len(df_filtered)
    
    # 随机抽取 num_trades 条记录
    sampled = df_filtered.sample(n=num_trades, random_state=seed).reset_index(drop=True)
    
    fund = initial_fund
    log = []
    for i, row in sampled.iterrows():
        r = row['第2天尾盘收益']
        profit = fund * r
        fund += profit
        log.append({
            "交易序号": i + 1,
            "交易日期": row['日期'].strftime("%Y-%m-%d"),
            "股票代码": row['股票代码'],
            "收益率": f"{r:.2%}",
            "收益金额": f"{profit:.2f}",
            "资金余额": f"{fund:.2f}"
        })
    
    df_log = pd.DataFrame(log)
    summary = {
        "初始资金": f"{initial_fund:.2f}",
        "最终资金": f"{fund:.2f}",
        "总收益": f"{fund - initial_fund:.2f}",
        "收益率": f"{(fund / initial_fund - 1):.2%}",
        "交易次数": num_trades
    }
    return summary, df_log
def run_fanbao_zhenfu_zt_model(file_path, start_date_filter, end_date_filter):
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
            df['是否涨停'] = (df['涨幅'] >= 0.097) & (df['涨幅'] <= 0.105)
            df['最高涨幅'] = df['最高'] / df['前收'] - 1
            df['是否涨停过'] = (df['最高涨幅'] >= 0.097) & (df['最高涨幅'] <= 0.105)
            df['是否炸板'] = df['收盘'] < df['最高']
            # df.at[i - 2, '是否涨停']
            for i in range(2, len(df) - 3):
                if not df.at[i - 2, '是否涨停']:
                    continue
                # if not df.at[i - 3, '是否涨停']:
                #     continue
                # if df.at[i - 4, '是否涨停'] & df.at[i - 3, '是否涨停']:
                #     continue
                # if not df.at[i - 1, '是否炸板'] & df.at[i - 1, '是否涨停过']:
                #     continue
                # if not df.at[i - 1, '收盘'] < df.at[i - 1, '开盘']:
                #     continue

                today_high = df.at[i, '最高']
                today_low = df.at[i, '最低']
                today_pre_close = df.at[i, '前收']
                today_high_1 = df.at[i - 1, '最高']
                today_low_1 = df.at[i - 1, '最低']
                today_pre_close_1 = df.at[i - 1, '前收']
                today_close = df.at[i, '收盘']
                today_open = df.at[i, '开盘']
                pre_complete = df.at[i - 2, '成交额']
                today_complete = df.at[i - 1, '成交额']
                if pd.isna(today_high) or pd.isna(today_low) or pd.isna(today_pre_close):
                    continue

                # 振幅 = (today_high - today_low) / today_pre_close # 打板日振幅
                # 振幅 = (today_high_1 - today_low_1) / today_pre_close_1 # 断板日振幅
                振幅 = (today_open / today_pre_close ) - 1 # 打板日开盘价振幅
                # 振幅 = today_complete / pre_complete # 量能振幅
                # 振幅 = df.at[i - 1, '涨幅'] # 断板日涨幅

                # 断板日振幅
                if not (0.015 <= (today_high_1 - today_low_1) / today_pre_close_1 <= 0.065):
                    continue
                # 断板日涨幅
                if not (0.015 <= df.at[i - 1, '涨幅'] <= 0.06):
                    continue
                # 打板日开盘价振幅
                if not (-0.06 <= 振幅 <= 0.0):
                    continue
                # 是否涨停过
                # limit_price = round(today_pre_close * 1.095, 2)
                # if not (round(today_close, 2) >= limit_price or round(today_high, 2) >= limit_price):
                #     continue

                record = {
                    '股票代码': code,
                    '日期': df.at[i - 1, '日期'],
                    '振幅': 振幅
                }

                buy_price = today_open
                if i + 1 < len(df):
                    open2, close2 = df.at[i + 1, '开盘'], df.at[i + 1, '收盘']
                    record['第2天开盘收益'] = (open2 / buy_price - 1) if pd.notna(open2) else np.nan
                    record['第2天尾盘收益'] = (close2 / buy_price - 1) if pd.notna(close2) else np.nan
                if i + 2 < len(df):
                    open3, close3 = df.at[i + 2, '开盘'], df.at[i + 2, '收盘']
                    record['第3天开盘收益'] = (open3 / buy_price - 1) if pd.notna(open3) else np.nan
                    record['第3天尾盘收益'] = (close3 / buy_price - 1) if pd.notna(close3) else np.nan

                all_data.append(record)
        except Exception as e:
            print(f"读取文件 {file} 出错：{e}")

    df_all = pd.DataFrame(all_data)
    df_all = df_all[(df_all['日期'] >= start_date_filter) & (df_all['日期'] <= end_date_filter)]
    if df_all.empty:
        print("❌ 没有符合条件的数据")
        return

    # 分箱振幅区间（-22% ~ 22%，每2%一档）
    bins = np.arange(-0.105, 0.105, 0.02)
    labels = [f"{int(left*100)}%–{int(right*100)}%" for left, right in zip(bins[:-1], bins[1:])]
    df_all['振幅区间'] = pd.cut(df_all['振幅'], bins=bins, labels=labels, include_lowest=True)

    # 聚合统计函数
    def calc_stats(df, col):
        avg = df[col].mean()
        win_rate = (df[col] > 0).mean()
        return pd.DataFrame({
            f"{col}平均收益": [avg],
            f"{col}胜率": [win_rate]
        })

    grouped = df_all.groupby('振幅区间').apply(lambda g: pd.concat([
        pd.DataFrame({'样本数': [len(g)]}),
        calc_stats(g, '第2天开盘收益'),
        calc_stats(g, '第2天尾盘收益'),
        calc_stats(g, '第3天开盘收益'),
        calc_stats(g, '第3天尾盘收益'),
    ], axis=1))

    grouped.reset_index(level=1, drop=True, inplace=True)
    grouped.index.name = '振幅区间'

    expected_cols = [
        '样本数',
        '第2天开盘收益平均收益', '第2天开盘收益胜率',
        '第2天尾盘收益平均收益', '第2天尾盘收益胜率',
        '第3天开盘收益平均收益', '第3天开盘收益胜率',
        '第3天尾盘收益平均收益', '第3天尾盘收益胜率',
    ]
    grouped = grouped[[col for col in expected_cols if col in grouped.columns]]

    print("\n📊 前一天跌5-10%，两天前涨停，当天涨停买入，次日/次次日收益情况（按振幅区间分类）")

    def format_color_all(x, col_name):
        return format_percent(x, is_rate='胜率' in col_name)

    def format_sign_all(x, col_name):
        return format_sign(x, is_rate='胜率' in col_name)

    grouped_fmt = grouped.copy()
    for col in grouped_fmt.columns:
        if col != '样本数':
            grouped_fmt[col] = grouped_fmt[col].apply(lambda x: format_color_all(x, col))
    grouped_print = grouped.copy()
    for col in grouped_print.columns:
        if col != '样本数':
            grouped_print[col] = grouped_print[col].apply(lambda x: format_sign_all(x, col))

    print(tabulate(grouped_fmt, headers='keys', tablefmt='psql', stralign='center'))

    sample_size = min(10, len(df_all))
    print("\n🔍 随机抽取10条原始记录供验证：")
    sample_df = df_all.sample(n=sample_size, random_state=42)
    for col in ['第2天开盘收益', '第2天尾盘收益', '第3天开盘收益', '第3天尾盘收益']:
        sample_df[col] = sample_df[col].apply(lambda x: f"{x * 100:.2f}%" if pd.notna(x) else "NaN")
    print(tabulate(sample_df[['股票代码', '日期', '振幅区间','振幅',
                              '第2天开盘收益', '第2天尾盘收益',
                              '第3天开盘收益', '第3天尾盘收益']], headers='keys', tablefmt='psql', stralign='center'))
    print(df_all.head())  # 可选：预览前几行结果

    summary, trade_log = simulate_from_df_random_trades(df_all, start_date="2022-12-01", end_date="2025-06-30", num_trades=1000, initial_fund=100000, seed=None)

    print("💰 模拟资金增长情况：")
    for k, v in summary.items():
        print(f"{k}: {v}")

    print("\n📈 随机抽取交易记录（前100条）：")
    print(trade_log.head(100))

    return grouped_print