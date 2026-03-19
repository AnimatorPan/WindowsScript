"""
应用优化 - 将优化后的播放器替换到主程序
"""
import shutil
import os
from pathlib import Path

def apply_optimization():
    """应用优化"""
    base_dir = Path(__file__).parent
    
    # 备份原始文件
    original = base_dir / "video_player.py"
    backup = base_dir / "video_player_original.py"
    optimized = base_dir / "video_player_optimized.py"
    
    if not optimized.exists():
        print("错误: 找不到优化版本文件")
        return False
    
    # 备份原始文件（如果还没备份）
    if not backup.exists():
        shutil.copy2(original, backup)
        print(f"✓ 已备份原始文件到: {backup}")
    
    # 替换为优化版本
    shutil.copy2(optimized, original)
    print(f"✓ 已应用优化版本")
    
    return True


def restore_original():
    """恢复原始版本"""
    base_dir = Path(__file__).parent
    
    original = base_dir / "video_player.py"
    backup = base_dir / "video_player_original.py"
    
    if not backup.exists():
        print("错误: 找不到备份文件")
        return False
    
    shutil.copy2(backup, original)
    print(f"✓ 已恢复原始版本")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_original()
    else:
        apply_optimization()
