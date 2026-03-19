"""
打包脚本 - 使用PyInstaller打包为可执行文件
"""
import PyInstaller.__main__
import os
import shutil
from pathlib import Path


def build():
    """构建可执行文件"""
    
    # 项目根目录
    project_dir = Path(__file__).parent
    
    # 清理之前的构建
    build_dir = project_dir / "build"
    dist_dir = project_dir / "dist"
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # FFmpeg路径
    ffmpeg_dir = project_dir / "ffmpeg"
    ffmpeg_files = []
    
    if ffmpeg_dir.exists():
        for file in ffmpeg_dir.iterdir():
            if file.suffix in ['.exe', '.dll']:
                ffmpeg_files.append(str(file))
    
    # PyInstaller参数
    args = [
        'main.py',
        '--name=视频转GIF工具',
        '--onefile',
        '--windowed',
        '--icon=NONE',
        f'--distpath={dist_dir}',
        f'--workpath={build_dir}',
        '--clean',
        '--noconfirm',
    ]
    
    # 添加数据文件
    # FFmpeg可执行文件
    for ffmpeg_file in ffmpeg_files:
        args.append(f'--add-binary={ffmpeg_file};ffmpeg')
    
    # 减少隐藏导入以加快启动速度
    # PyQt6的依赖会自动处理
    
    print("开始打包...")
    print(f"FFmpeg文件: {ffmpeg_files}")
    
    # 运行PyInstaller
    PyInstaller.__main__.run(args)
    
    print("\n打包完成!")
    print(f"输出目录: {dist_dir}")


if __name__ == "__main__":
    build()
