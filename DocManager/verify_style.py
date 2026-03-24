"""
验证样式加载
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QLabel, QPushButton, QLineEdit
)


def test_style():
    """测试样式"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 加载样式
    from utils.style_manager import StyleManager
    
    style_manager = StyleManager()
    print(f"样式目录: {style_manager.get_styles_dir()}")
    print(f"样式目录存在: {style_manager.get_styles_dir().exists()}")
    
    style_manager.load_theme(StyleManager.DARK_THEME)
    print(f"当前主题: {style_manager.get_current_theme()}")
    
    # 创建测试窗口
    window = QMainWindow()
    window.setWindowTitle("样式测试")
    window.resize(400, 300)
    
    central = QWidget()
    window.setCentralWidget(central)
    
    layout = QVBoxLayout(central)
    
    layout.addWidget(QLabel("如果这是深色背景，说明主题加载成功 ✓"))
    layout.addWidget(QLineEdit())
    layout.addWidget(QPushButton("测试按钮"))
    
    # 切换按钮
    toggle_btn = QPushButton("切换主题")
    toggle_btn.clicked.connect(style_manager.switch_theme)
    layout.addWidget(toggle_btn)
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    test_style()