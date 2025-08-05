# 主要运行文件 main.py
#
#
from import_all import save_log_to_top, run_model1,run_model2,run_drop20_model,run_zhaban_zt_buy_next_day_model,run_lianban_buy_model,run_zhuangting_fanbao_model,run_fanbao_drop5to10_prev_zt_model,run_fanbao_zhenfu_zt_model
from load_data import file_path, cache_path, start_date_filter, end_date_filter


# === 调用策略方法 ===
result_str = run_fanbao_zhenfu_zt_model(file_path, start_date_filter, end_date_filter)
# print(result_str)

# === 打印到日志顶部 ===
data_during = f"{start_date_filter.strftime('%Y-%m-%d')} 至 {end_date_filter.strftime('%Y-%m-%d')}"
save_log_to_top(result_str.to_string(), title="炸板次日涨停买入策略回测结果",data_during=data_during)
