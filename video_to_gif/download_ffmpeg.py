"""
FFmpeg下载脚本
运行此脚本下载FFmpeg到项目目录
"""
import urllib.request
import zipfile
import os
import shutil
from pathlib import Path


def download_ffmpeg():
    """下载并解压FFmpeg"""
    
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = "ffmpeg_temp.zip"
    
    print("正在下载FFmpeg...")
    print(f"下载地址: {ffmpeg_url}")
    
    try:
        # 下载文件
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        print(f"下载完成: {zip_path}")
        
        # 解压
        print("正在解压...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("ffmpeg_temp")
        
        # 找到解压后的目录
        temp_dir = Path("ffmpeg_temp")
        ffmpeg_dirs = list(temp_dir.glob("ffmpeg-*"))
        
        if not ffmpeg_dirs:
            print("错误: 找不到FFmpeg目录")
            return False
        
        ffmpeg_dir = ffmpeg_dirs[0]
        bin_dir = ffmpeg_dir / "bin"
        
        # 创建目标目录
        target_dir = Path("video_to_gif/ffmpeg")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制需要的文件
        files_to_copy = ['ffmpeg.exe', 'ffprobe.exe']
        for filename in files_to_copy:
            src = bin_dir / filename
            dst = target_dir / filename
            if src.exists():
                shutil.copy2(src, dst)
                print(f"已复制: {filename}")
        
        # 清理临时文件
        os.remove(zip_path)
        shutil.rmtree("ffmpeg_temp")
        
        print("\nFFmpeg安装完成!")
        print(f"安装位置: {target_dir.absolute()}")
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        # 清理临时文件
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists("ffmpeg_temp"):
            shutil.rmtree("ffmpeg_temp")
        return False


if __name__ == "__main__":
    download_ffmpeg()
