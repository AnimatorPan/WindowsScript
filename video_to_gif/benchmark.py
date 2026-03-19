"""
视频加载性能基准测试
对比原始版本和优化版本的加载速度
"""
import time
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def benchmark_original(video_path: str):
    """测试原始版本"""
    print("=" * 60)
    print("测试原始版本...")
    print("=" * 60)
    
    from video_player import VideoPlayer
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    player = VideoPlayer()
    
    start_time = time.time()
    result = player.load_video(video_path)
    end_time = time.time()
    
    elapsed = end_time - start_time
    
    if result:
        print(f"✓ 加载成功")
        print(f"  耗时: {elapsed:.2f}秒")
        print(f"  视频时长: {player.duration:.2f}秒")
        print(f"  视频尺寸: {player.video_size}")
        print(f"  提取帧数: {len(player.frame_files)}")
    else:
        print(f"✗ 加载失败")
    
    player.cleanup()
    
    return elapsed if result else None


def benchmark_optimized(video_path: str):
    """测试优化版本"""
    print("\n" + "=" * 60)
    print("测试优化版本...")
    print("=" * 60)
    
    from video_player_optimized import VideoPlayer
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread, QEventLoop
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    player = VideoPlayer()
    
    # 记录各阶段时间
    timings = {}
    
    def on_info_ready(info):
        timings['info_ready'] = time.time()
        print(f"  视频信息获取: {(timings['info_ready'] - timings['start'])*1000:.0f}ms")
    
    def on_first_frame(path):
        timings['first_frame'] = time.time()
        print(f"  首帧显示: {(timings['first_frame'] - timings['start'])*1000:.0f}ms")
    
    def on_all_frames(frames):
        timings['all_frames'] = time.time()
        print(f"  全部帧加载: {(timings['all_frames'] - timings['start'])*1000:.0f}ms")
        print(f"  提取帧数: {len(frames)}")
    
    player.load_worker.info_ready.connect(on_info_ready)
    player.load_worker.first_frame_ready.connect(on_first_frame)
    player.load_worker.all_frames_ready.connect(on_all_frames)
    
    timings['start'] = time.time()
    result = player.load_video(video_path)
    
    # 等待加载完成
    if result:
        loop = QEventLoop()
        player.load_worker.all_frames_ready.connect(lambda _: loop.quit())
        player.load_worker.error_occurred.connect(lambda _: loop.quit())
        
        # 最多等待60秒
        QThread.msleep(100)
        loop.exec()
    
    end_time = time.time()
    elapsed = end_time - timings['start']
    
    if result and player.duration > 0:
        print(f"✓ 加载成功")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  视频时长: {player.duration:.2f}秒")
        print(f"  视频尺寸: {player.video_size}")
    else:
        print(f"✗ 加载失败")
    
    player.cleanup()
    
    return elapsed if result else None


def main():
    """主函数"""
    print("视频加载性能基准测试")
    print("=" * 60)
    
    # 查找测试视频
    test_videos = [
        r"G:\GitHub\WindowsScript\video_to_gif\test_video.mp4",
        r"G:\test_video.mp4",
        r"test_video.mp4",
    ]
    
    video_path = None
    for v in test_videos:
        if os.path.exists(v):
            video_path = v
            break
    
    if not video_path:
        print("错误: 找不到测试视频文件")
        print("请提供一个视频文件路径作为参数")
        print(f"用法: python benchmark.py <视频路径>")
        return
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return
    
    print(f"测试视频: {video_path}")
    print(f"文件大小: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")
    print()
    
    # 测试原始版本
    original_time = benchmark_original(video_path)
    
    # 测试优化版本
    optimized_time = benchmark_optimized(video_path)
    
    # 对比结果
    print("\n" + "=" * 60)
    print("性能对比")
    print("=" * 60)
    
    if original_time and optimized_time:
        speedup = original_time / optimized_time
        improvement = (1 - optimized_time / original_time) * 100
        
        print(f"原始版本: {original_time:.2f}秒")
        print(f"优化版本: {optimized_time:.2f}秒")
        print(f"速度提升: {speedup:.1f}x")
        print(f"时间减少: {improvement:.1f}%")
    else:
        print("测试未完成")


if __name__ == "__main__":
    main()
