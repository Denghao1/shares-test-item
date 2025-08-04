# 方法引入文件
#
#
import sys
import os

# === 加入 until 路径 ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'until')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'item')))

# === 引入工具函数 ===
from log_utils import save_log_to_top

# === 引入回测策略 ===
from model1 import run_model1
from model2 import run_model2
from model3 import run_drop20_model
from model4 import run_zhaban_zt_buy_next_day_model
from model5 import run_lianban_buy_model
from model6 import run_zhuangting_fanbao_model
from model7 import run_fanbao_drop5to10_prev_zt_model
__all__ = ['save_log_to_top', 'run_model1','run_model2','run_drop20_model','run_zhaban_zt_buy_next_day_model','run_lianban_buy_model','run_zhuangting_fanbao_model','run_fanbao_drop5to10_prev_zt_model']
