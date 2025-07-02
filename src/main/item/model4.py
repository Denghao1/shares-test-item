# 炸板次日涨停买入策略回测结果

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

def run_zhaban_zt_buy_next_day_model(file_path, start_date_filter, end_date_filter):
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

            df['前收'] = df['收盘'].shift(1)
            df['涨跌幅'] = df['收盘'] / df['前收'] - 1
            df['最高涨幅'] = df['最高'] / df['前收'] - 1

            # 判断炸板（前一日收盘未封涨停但盘中摸到涨停）
            df['是否炸板'] = (df['最高涨幅'] >= 0.099) & (df['涨跌幅'] < 0.099) & (df['最高涨幅'] <= 0.105)

            for idx in df[df['是否炸板']].index:
                if idx + 3 >= len(df):
                    continue

                next_day_return = df.at[idx + 1, '最高涨幅']
                if next_day_return >= 0.099:  # 次日涨停过
                    record = {
                        '股票代码': code,
                        '炸板日期': df.at[idx, '日期'],
                        '次日涨停日期': df.at[idx + 1, '日期']
                    }

                    buy_price = df.at[idx + 1, '最高']
                    # 第三天尾盘收益
                    close3 = df.at[idx + 2, '收盘']
                    record['第3日尾盘卖出收益'] = (close3 / buy_price - 1) if buy_price and close3 else np.nan

                    # 第四天开盘收益
                    open4 = df.at[idx + 3, '开盘']
                    record['第4日开盘卖出收益'] = (open4 / buy_price - 1) if buy_price and open4 else np.nan

                    # 第四天尾盘收益
                    close4 = df.at[idx + 3, '收盘']
                    record['第4日尾盘卖出收益'] = (close4 / buy_price - 1) if buy_price and close4 else np.nan

                    all_stock.append(record)

        except Exception as e:
            print(f"读取文件 {file} 出错：{e}")

    df_all = pd.DataFrame(all_stock)
    df_all = df_all[(df_all['炸板日期'] >= start_date_filter) & (df_all['炸板日期'] <= end_date_filter)]

    if df_all.empty:
        return "❌ 无满足条件的数据"

    print(f"\n🎯 满足策略的股票数量：{len(df_all)}")

    result = pd.DataFrame()
    result.loc['统计', '第3日尾盘平均收益'] = df_all['第3日尾盘卖出收益'].mean()
    result.loc['统计', '第4日开盘平均收益'] = df_all['第4日开盘卖出收益'].mean()
    result.loc['统计', '第4日尾盘平均收益'] = df_all['第4日尾盘卖出收益'].mean()

    print("\n📊 平均收益统计：")
    print(result.fillna(0).to_string(float_format="{:.2%}".format))

    print("\n🏆 前20个最大收益记录（按第4日尾盘卖出收益排序）：")
    print(
        df_all.sort_values('第4日尾盘卖出收益', ascending=False)
              .head(20)[['股票代码', '炸板日期', '第3日尾盘卖出收益', '第4日开盘卖出收益', '第4日尾盘卖出收益']]
              .to_string(index=False, float_format="{:.2%}".format)
    )

    return result
