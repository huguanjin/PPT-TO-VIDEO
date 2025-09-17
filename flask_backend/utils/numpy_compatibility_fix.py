"""
临时解决方案：处理spaCy与NumPy兼容性问题
通过设置环境变量来抑制NumPy版本警告
"""

import warnings
import os
import sys

# 抑制所有NumPy相关的警告
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")
warnings.filterwarnings("ignore", message=".*numpy.dtype size changed.*")
warnings.filterwarnings("ignore", message=".*numpy.ufunc size changed.*")
warnings.filterwarnings("ignore", message=".*binary incompatibility.*")

# 设置环境变量
os.environ['PYTHONWARNINGS'] = 'ignore::RuntimeWarning:numpy,ignore::UserWarning:numpy'
os.environ['NPY_DISABLE_NUMPY_1_WARNINGS'] = '1'

# 尝试在导入numpy之前设置
try:
    import numpy as np
    # 抑制numpy的二进制不兼容性警告
    np.warnings.filterwarnings('ignore')
except ImportError:
    pass

print("NumPy警告抑制模块已加载")