#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本：将按键精灵程序打包成可执行文件
"""

import os
import sys
import shutil
import subprocess


def clean_build():
    """清理之前的构建文件"""
    dirs_to_remove = ['build', 'dist']
    files_to_remove = ['按键精灵.spec']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除: {dir_name}")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"已删除: {file_name}")


def build_exe():
    """打包 exe 文件"""
    
    # 清理之前的构建
    clean_build()
    
    # PyInstaller 参数
    args = [
        'pyinstaller',
        '--name=按键精灵',
        '--windowed',  # 使用窗口模式，不显示控制台
        '--onefile',   # 打包成单个文件
        '--clean',     # 清理临时文件
        '--noconfirm', # 不确认覆盖
        
        # 添加数据文件
        '--add-data', 'core;core',
        '--add-data', 'gui;gui',
        '--add-data', 'utils;utils',
        
        # 隐藏导入的模块
        '--hidden-import', 'core.action',
        '--hidden-import', 'core.executor',
        '--hidden-import', 'core.preset',
        '--hidden-import', 'gui.main_window',
        '--hidden-import', 'utils.window_helper',
        
        # 图标（如果有的话）
        # '--icon=icon.ico',
        
        # 主程序入口
        'main.py'
    ]
    
    print("开始打包...")
    print(f"命令: {' '.join(args)}")
    print()
    
    try:
        result = subprocess.run(args, check=True, capture_output=False)
        print("\n打包成功！")
        print(f"可执行文件位置: {os.path.abspath('dist/按键精灵.exe')}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        return False


def create_batch_file():
    """创建运行批处理文件"""
    batch_content = '''@echo off
chcp 65001 >nul
cd /d "%~dp0"
start "" "按键精灵.exe"
'''
    
    with open('dist/运行按键精灵.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    print("已创建: dist/运行按键精灵.bat")


def main():
    """主函数"""
    print("=" * 50)
    print("按键精灵 - 打包工具")
    print("=" * 50)
    print()
    
    # 检查当前目录
    if not os.path.exists('main.py'):
        print("错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 打包
    if build_exe():
        create_batch_file()
        print()
        print("=" * 50)
        print("打包完成！")
        print("=" * 50)
        print()
        print("文件位置:")
        print(f"  - 可执行文件: {os.path.abspath('dist/按键精灵.exe')}")
        print(f"  - 运行脚本: {os.path.abspath('dist/运行按键精灵.bat')}")
        print()
        print("使用方法:")
        print("  1. 直接双击 '按键精灵.exe' 运行")
        print("  2. 或双击 '运行按键精灵.bat' 运行")
        print()
        print("提示:")
        print("  - 首次运行可能需要几秒钟启动")
        print("  - 可以将 exe 文件复制到任何地方使用")
    else:
        print("\n打包失败，请检查错误信息")
        sys.exit(1)


if __name__ == '__main__':
    main()
