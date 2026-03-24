"""
测试运行脚本（更新版）
"""
import sys
import pytest
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("DocManager 完整测试套件")
    print("=" * 60)
    
    args = [
        "tests/",
        "-v",
        "--tb=short",
        "-s",
        "--durations=10",  # 显示最慢的 10 个测试
    ]
    
    result = pytest.main(args)
    
    print("\n" + "=" * 60)
    if result == 0:
        print("✓ 所有测试通过")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    sys.exit(run_tests())