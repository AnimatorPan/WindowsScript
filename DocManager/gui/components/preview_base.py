"""
文档预览基类
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PreviewWidget(QWidget):
    """预览组件基类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.preview_area = QLabel("选择文档查看预览")
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setStyleSheet("color: #888; font-size: 11pt;")
        layout.addWidget(self.preview_area)

    def load_file(self, file_path: str):
        self.current_file = file_path
        if not Path(file_path).exists():
            self.show_error("文件不存在")
            return
        self.do_preview(file_path)

    def do_preview(self, file_path: str):
        raise NotImplementedError

    def clear(self):
        self.preview_area.setText("选择文档查看预览")
        self.current_file = None

    def show_error(self, message: str):
        self.preview_area.setText(f"⚠️ {message}")