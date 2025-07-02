# 日志方法

import os
from datetime import datetime

def save_log_to_top(log_content: str, title: str = "日志记录",data_during:str = "", log_dir: str = "src/log", log_file: str = "log.txt"):
    """
    将日志内容写入 log/log.txt 的最顶部，附带时间与标题
    :param log_content: 要写入的文本内容
    :param title: 日志标题
    :param log_dir: 日志目录
    :param log_file: 日志文件名
    """
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, log_file)

    # 时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"【{title}】 {timestamp}\n"
    dateDuring = f"(时间段: {data_during})\n"

    # 新内容 + 旧内容
    new_entry = header + dateDuring + log_content.strip() + "\n" + "="*60 + "\n"

    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            old_content = f.read()
    else:
        old_content = ""

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_entry + old_content)




