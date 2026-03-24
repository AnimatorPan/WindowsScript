"""
PDF 文件预览
"""
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import logging

from .preview_base import PreviewWidget

logger = logging.getLogger(__name__)


class PDFPreview(PreviewWidget):
    """PDF 预览"""

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setText("选择 PDF 查看预览")
        self.scroll_area.setWidget(self.preview_label)

        layout.addWidget(self.scroll_area)

    def do_preview(self, file_path: str):
        try:
            import fitz

            doc = fitz.open(file_path)
            if len(doc) == 0:
                self.show_error("PDF 文件为空")
                return

            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            img = QImage(
                pix.samples, pix.width, pix.height,
                pix.stride, QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(img)

            if pixmap.width() > 800:
                pixmap = pixmap.scaledToWidth(
                    800, Qt.TransformationMode.SmoothTransformation
                )

            self.preview_label.setPixmap(pixmap)
            doc.close()

        except ImportError:
            self.preview_label.setText(
                "PDF 预览需要安装 PyMuPDF\n\n"
                "请运行: pip install PyMuPDF"
            )
        except Exception as e:
            logger.error(f"预览 PDF 失败: {e}")
            self.show_error(f"预览失败: {e}")

    def clear(self):
        self.preview_label.clear()
        self.preview_label.setText("选择 PDF 查看预览")
        self.current_file = None