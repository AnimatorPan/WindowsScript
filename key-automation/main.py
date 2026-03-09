import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """程序入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("按键精灵自动化工具")
    app.setApplicationVersion("1.0.0")
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
