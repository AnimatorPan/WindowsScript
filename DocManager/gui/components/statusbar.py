"""
状态栏组件（简化版）
"""
from PyQt6.QtWidgets import QStatusBar, QLabel


class StatusBar(QStatusBar):
    """状态栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.message_label = QLabel("就绪")
        self.addWidget(self.message_label)
        
        # 右侧信息
        self.info_label = QLabel("")
        self.addPermanentWidget(self.info_label)
    
    def show_message(self, message: str, timeout: int = 0):
        """显示消息"""
        self.message_label.setText(message)
        if timeout > 0:
            super().showMessage(message, timeout)
    
    def set_info(self, info: str):
        """设置右侧信息"""
        self.info_label.setText(info)