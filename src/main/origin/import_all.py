import sys
import os

# until 文件夹位于 origin 的“同级兄弟”目录
until_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'until'))
sys.path.append(until_path)

from log_utils import save_log_to_top

__all__ = ['save_log_to_top']
