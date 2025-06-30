# 主要运行文件 main.py
#
#
from import_all import save_log_to_top, run_model1
from load_data import file_path, cache_path, start_date_filter, end_date_filter


# === 调用策略方法 ===
result_str = run_model1(file_path, cache_path, start_date_filter, end_date_filter)
print(result_str)

# === 打印到日志顶部 ===
save_log_to_top(result_str, title="炸板策略回测结果2")
