"""
图片文件预览
"""
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import logging

from .preview_base import PreviewWidget

logger = logging.getLogger(__name__)


class ImagePreview(PreviewWidget):
    """图片预览"""

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("选择图片查看预览")
        self.scroll_area.setWidget(self.image_label)

        layout.addWidget(self.scroll_area)

    def do_preview(self, file_path: str):
        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                self.show_error("无法加载图片")
                return

            if pixmap.width() > 800 or pixmap.height() > 600:
                pixmap = pixmap.scaled(
                    800, 600,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            self.image_label.setPixmap(pixmap)
        except Exception as e:
            logger.error(f"预览图片失败: {e}")
            self.show_error(f"预览失败: {e}")

    def clear(self):
        self.image_label.clear()
        self.image_label.setText("选择图片查看预览")
        self.current_file = None