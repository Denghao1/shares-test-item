# 策略回测结果

import pandas as pd
import numpy as np
import os
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

def run_drop20_model(file_path, start_date_filter, end_date_filter):
    all_stock = []

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

            df['3日跌幅'] = df['收盘'].pct_change(3)

            for idx in df.index:
                if idx < 3:
                    continue

                drop_pct = df.at[idx, '3日跌幅']
                if drop_pct is not None and drop_pct <= -0.20:
                    record = {
                        '股票代码': code,
                        '日期': df.at[idx, '日期']
                    }

                    for offset in [1, 2]:  # 第4天=idx+1, 第5天=idx+2
                        if idx + offset >= len(df):
                            break
                        day = f'第{offset+3}天'
                        open_price = df.at[idx + offset, '开盘']
                        close_price = df.at[idx + offset, '收盘']
                        pre_close = df.at[idx + offset - 1, '收盘']

                        record[f'{day}开盘涨幅'] = (open_price / pre_close - 1) \
                            if pd.notna(open_price) and pd.notna(pre_close) and pre_close != 0 else np.nan
                        record[f'{day}收益'] = (close_price / open_price - 1) \
                            if pd.notna(open_price) and pd.notna(close_price) and open_price != 0 else np.nan

                    all_stock.append(record)

        except Exception as e:
            print(f"读取文件 {file} 出错：{e}")

    # ==== 整合数据 ====
    df_all = pd.DataFrame(all_stock)
    df_all = df_all[
        (df_all['日期'] >= start_date_filter) & (df_all['日期'] <= end_date_filter)
    ]

    if df_all.empty:
        print("❌ 无满足条件的股票数据。")
        return None

    # ==== 总数 ====
    print(f"\n🎯 满足3日跌幅 ≥ 20%的可交易股票总数：{len(df_all)} 只")

    # ==== 平均值统计 ====
    result = pd.DataFrame()
    for offset in [1, 2]:
        day = f'第{offset+3}天'
        result.loc[day, '平均开盘涨幅'] = df_all[f'{day}开盘涨幅'].mean()
        result.loc[day, '平均收益'] = df_all[f'{day}收益'].mean()

    print("\n📊 平均收益统计：")
    print(result.fillna(0).to_string(float_format="{:.2%}".format))

    # ==== Top 20 总收益 ====
    df_all['总收益'] = df_all[['第4天收益', '第5天收益']].sum(axis=1, skipna=False)
    top_20 = df_all.sort_values('总收益', ascending=False).head(20)

    print("\n🏆 前20个最大收益记录：")
    print(top_20[['股票代码', '日期', '第4天收益', '第5天收益', '总收益']]
          .to_string(index=False, float_format="{:.2%}".format))

    return result
