#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件批量复制工具 - 主程序入口

功能：从源文件夹复制同名同格式文件到目标文件夹
仅复制目标文件夹中已存在的同名文件
"""

import sys
from pathlib import Path

# 添加父目录到路径（用于直接运行）
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_copier.gui import main

if __name__ == '__main__':
    main()
