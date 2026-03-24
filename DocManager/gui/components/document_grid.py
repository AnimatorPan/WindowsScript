"""
文档网格视图组件
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel,
    QScrollArea, QFrame, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# 文件类型颜色映射
FILE_TYPE_COLORS = {
    'pdf': '#f44336',
    'doc': '#2196f3',
    'docx': '#2196f3',
    'xls': '#4caf50',
    'xlsx': '#4caf50',
    'ppt': '#ff9800',
    'pptx': '#ff9800',
    'txt': '#9e9e9e',
    'md': '#607d8b',
    'jpg': '#9c27b0',
    'jpeg': '#9c27b0',
    'png': '#9c27b0',
    'gif': '#9c27b0',
}


class DocumentCard(QFrame):
    """文档卡片组件"""
    
    clicked = pyqtSignal(int)  # 文档 ID
    double_clicked = pyqtSignal(int)
    right_clicked = pyqtSignal(int, object)  # 文档 ID, 位置
    
    def __init__(self, document: dict, parent=None):
        super().__init__(parent)
        
        self.document = document
        self.selected = False
        
        self.init_ui()
        self.apply_style()
    
    def init_ui(self):
        """初始化界面"""
        self.setFixedSize(140, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda pos: self.right_clicked.emit(self.document['id'], self.mapToGlobal(pos))
        )
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 文件图标区
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(80, 80)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.generate_icon()
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 文件名
        filename = self.document.get('filename', '')
        if len(filename) > 16:
            filename = filename[:14] + "..."
        
        self.name_label = QLabel(filename)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setToolTip(self.document.get('filename', ''))
        layout.addWidget(self.name_label)
        
        # 文件类型标签
        file_type = self.document.get('file_type', 'unknown') or 'unknown'
        self.type_label = QLabel(file_type.upper())
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        color = FILE_TYPE_COLORS.get(file_type.lower(), '#9e9e9e')
        self.type_label.setStyleSheet(
            f"color: white; background-color: {color}; "
            "border-radius: 3px; padding: 1px 5px; font-size: 8pt;"
        )
        layout.addWidget(self.type_label, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def generate_icon(self):
        """生成文件类型图标"""
        file_type = self.document.get('file_type', 'unknown') or 'unknown'
        color = FILE_TYPE_COLORS.get(file_type.lower(), '#9e9e9e')
        
        # 创建图标
        pixmap = QPixmap(80, 80)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制文件图标背景
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(5, 5, 65, 70, 5, 5)
        
        # 绘制折角
        painter.setBrush(QColor(255, 255, 255, 80))
        fold_points = [
            (50, 5),
            (70, 25),
            (70, 25),
            (50, 25),
            (50, 5),
        ]
        from PyQt6.QtGui import QPolygon
        from PyQt6.QtCore import QPoint
        
        poly = QPolygon([QPoint(x, y) for x, y in fold_points])
        painter.drawPolygon(poly)
        
        # 绘制文件类型文字
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        
        ext = file_type.upper()[:4]
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, ext)
        
        painter.end()
        
        self.icon_label.setPixmap(pixmap)
    
    def apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            DocumentCard {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 6px;
            }
            DocumentCard:hover {
                background-color: #4a4a4a;
                border-color: #0d7377;
            }
        """)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.selected = selected
        
        if selected:
            self.setStyleSheet("""
                DocumentCard {
                    background-color: #0d7377;
                    border: 2px solid #0d7377;
                    border-radius: 6px;
                }
            """)
        else:
            self.apply_style()
    
    def mousePressEvent(self, event):
        """鼠标点击"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.document['id'])
        
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.document['id'])
        
        super().mouseDoubleClickEvent(event)


class DocumentGridWidget(QWidget):
    """文档网格视图组件"""
    
    document_selected = pyqtSignal(int)
    selection_changed = pyqtSignal(int)
    documents_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_window = parent
        self.documents = []
        self.cards = {}  # doc_id -> DocumentCard
        self.selected_ids = set()
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 网格容器
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)
        
        # 空状态提示
        self.empty_label = QLabel("暂无文档")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; font-size: 14pt;")
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)
    
    def load_documents(self, documents: list):
        """加载文档列表"""
        self.documents = documents
        self.selected_ids.clear()
        self.cards.clear()
        
        # 清除旧卡片
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not documents:
            self.empty_label.setVisible(True)
            return
        
        self.empty_label.setVisible(False)
        
        # 计算列数（根据宽度动态调整）
        cols = max(2, self.scroll_area.width() // 160)
        
        for idx, doc in enumerate(documents):
            row = idx // cols
            col = idx % cols
            
            card = DocumentCard(doc, self)
            card.clicked.connect(self.on_card_clicked)
            card.double_clicked.connect(self.on_card_double_clicked)
            card.right_clicked.connect(self.on_card_right_clicked)
            
            self.grid_layout.addWidget(card, row, col)
            self.cards[doc['id']] = card
        
        logger.info(f"网格视图加载了 {len(documents)} 个文档")
    
    def on_card_clicked(self, doc_id: int):
        """卡片点击"""
        # 取消其他选中
        for card_id, card in self.cards.items():
            if card_id != doc_id:
                card.set_selected(False)
        
        self.selected_ids = {doc_id}
        self.cards[doc_id].set_selected(True)
        
        self.document_selected.emit(doc_id)
        self.selection_changed.emit(1)
    
    def on_card_double_clicked(self, doc_id: int):
        """卡片双击（打开文档）"""
        self.open_document(doc_id)
    
    def on_card_right_clicked(self, doc_id: int, pos):
        """卡片右击"""
        menu = QMenu(self)
        
        from PyQt6.QtGui import QAction
        
        open_action = QAction("打开", self)
        open_action.triggered.connect(lambda: self.open_document(doc_id))
        menu.addAction(open_action)
        
        menu.addSeparator()
        
        add_cat_action = QAction("添加到分类...", self)
        add_cat_action.triggered.connect(lambda: self.add_to_category([doc_id]))
        menu.addAction(add_cat_action)
        
        add_tag_action = QAction("添加标签...", self)
        add_tag_action.triggered.connect(lambda: self.add_tags([doc_id]))
        menu.addAction(add_tag_action)
        
        menu.addSeparator()
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_documents([doc_id]))
        menu.addAction(delete_action)
        
        menu.exec(pos)
    
    def open_document(self, doc_id: int):
        """打开文档"""
        if not self.main_window or not self.main_window.db:
            return
        
        from core.document import DocumentManager
        import os
        import platform
        
        try:
            doc_manager = DocumentManager(self.main_window.db, self.main_window.library_id)
            doc = doc_manager.get(doc_id)
            
            if not doc:
                return
            
            storage_path = Path(self.main_window.current_library['storage_path'])
            file_path = storage_path / doc['filepath']
            
            if not file_path.exists():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "错误", f"文件不存在:\n{file_path}")
                return
            
            if platform.system() == 'Windows':
                os.startfile(str(file_path))
            elif platform.system() == 'Darwin':
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')
        
        except Exception as e:
            logger.error(f"打开文档失败: {e}")
    
    def add_to_category(self, document_ids: list):
        """添加到分类"""
        from gui.dialogs.batch_operation_dialog import BatchOperationDialog
        
        dialog = BatchOperationDialog(
            self.main_window.db,
            self.main_window.library_id,
            document_ids,
            self
        )
        
        if dialog.exec():
            self.documents_updated.emit()
    
    def add_tags(self, document_ids: list):
        """添加标签"""
        from gui.dialogs.batch_operation_dialog import BatchOperationDialog
        
        dialog = BatchOperationDialog(
            self.main_window.db,
            self.main_window.library_id,
            document_ids,
            self
        )
        
        if dialog.exec():
            self.documents_updated.emit()
    
    def delete_documents(self, document_ids: list):
        """删除文档"""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {len(document_ids)} 个文档吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from core.document import DocumentManager
            
            doc_manager = DocumentManager(self.main_window.db, self.main_window.library_id)
            
            for doc_id in document_ids:
                try:
                    doc_manager.delete(doc_id)
                except Exception as e:
                    logger.error(f"删除文档失败: {e}")
            
            self.documents_updated.emit()
    
    def get_selected_document_ids(self) -> list:
        """获取选中的文档ID"""
        return list(self.selected_ids)
    
    def resizeEvent(self, event):
        """窗口大小改变时重新布局"""
        super().resizeEvent(event)
        
        if self.documents:
            self.load_documents(self.documents)