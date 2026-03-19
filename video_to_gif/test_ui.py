"""
简单UI测试
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试UI")
        self.setMinimumSize(600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        label = QLabel("这是一个测试标签")
        layout.addWidget(label)
        
        button = QPushButton("测试按钮")
        layout.addWidget(button)
        
        print("UI 初始化完成")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("窗口显示")
    sys.exit(app.exec())
