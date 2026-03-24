"""
打包脚本 - 使用 PyInstaller 创建可执行文件
"""
import sys
import os
from pathlib import Path
import shutil


def clean_build():
    """清理构建目录"""
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ 清理 {dir_name}/")


def build_exe():
    """构建可执行文件"""
    print("=" * 60)
    print("DocManager 打包工具")
    print("=" * 60)
    
    # 清理旧构建
    print("\n1. 清理旧构建...")
    clean_build()
    
    # 确定虚拟环境 Python 路径
    venv_python = sys.executable
    venv_pyinstaller = Path(venv_python).parent / "pyinstaller.exe"
    
    # 如果找不到 pyinstaller.exe，尝试用 python -m pyinstaller
    if not venv_pyinstaller.exists():
        pyinstaller_cmd = [venv_python, "-m", "PyInstaller"]
    else:
        pyinstaller_cmd = [str(venv_pyinstaller)]
    
    # PyInstaller 参数
    print("\n2. 开始打包...")
    print(f"   使用 Python: {venv_python}")
    
    cmd = pyinstaller_cmd + [
        '--name=DocManager',
        '--windowed',  # GUI 应用，无控制台窗口
        '--onefile',   # 打包成单个文件
        '--clean',     # 清理临时文件
        '--noconfirm', # 不确认覆盖
        # 应用图标
        '--icon=assets/icons/app.ico',
        # 添加数据文件
        '--add-data', 'core/schema.sql;core',
        '--add-data', 'assets/icons/app.ico;assets/icons',
        # 隐藏导入
        '--hidden-import', 'PyQt6.sip',
        '--hidden-import', 'PyQt6.QtCore',
        '--hidden-import', 'PyQt6.QtGui',
        '--hidden-import', 'PyQt6.QtWidgets',
        # 主程序入口
        'main.py'
    ]
    
    import subprocess
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✓ 打包成功!")
        print("=" * 60)
        print(f"\n可执行文件位置: {Path('dist/DocManager.exe').absolute()}")
        print("\n可以复制到任何地方运行，无需 Python 环境")
    else:
        print("\n✗ 打包失败")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(build_exe())
