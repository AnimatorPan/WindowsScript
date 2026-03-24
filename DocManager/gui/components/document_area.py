"""
文档内容区 - 整合列表视图和网格视图
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt
import logging

from .document_list import DocumentListWidget
from .document_grid import DocumentGridWidget

logger = logging.getLogger(__name__)


class DocumentArea(QWidget):
    """文档内容区"""
    
    document_selected = pyqtSignal(int)
    selection_changed = pyqtSignal(int)
    documents_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_window = parent
        self.current_view = 'list'
        self.documents = []
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 视图控制栏
        control_bar = self.create_control_bar()
        layout.addWidget(control_bar)
        
        # 视图栈
        self.stack = QStackedWidget()
        
        # 列表视图
        self.list_view = DocumentListWidget(self)
        self.list_view.document_selected.connect(self.document_selected)
        self.list_view.selection_changed.connect(self.selection_changed)
        self.list_view.documents_updated.connect(self.documents_updated)
        self.stack.addWidget(self.list_view)
        
        # 网格视图
        self.grid_view = DocumentGridWidget(self)
        self.grid_view.document_selected.connect(self.document_selected)
        self.grid_view.selection_changed.connect(self.selection_changed)
        self.grid_view.documents_updated.connect(self.documents_updated)
        self.stack.addWidget(self.grid_view)
        
        layout.addWidget(self.stack)
        
        # 默认列表视图
        self.switch_view('list')
    
    def create_control_bar(self):
        """创建控制栏"""
        bar = QWidget()
        bar.setMaximumHeight(40)
        bar.setStyleSheet("background-color: #3c3c3c; border-bottom: 1px solid #555;")
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # 文档计数
        self.count_label = QLabel("0 个文档")
        self.count_label.setStyleSheet("color: #888;")
        layout.addWidget(self.count_label)
        
        layout.addStretch()
        
        # 排序
        sort_label = QLabel("排序:")
        sort_label.setStyleSheet("color: #888;")
        layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["导入时间↓", "导入时间↑", "文件名↑", "文件名↓", "大小↓", "大小↑"])
        self.sort_combo.setMaximumWidth(120)
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        layout.addWidget(self.sort_combo)
        
        layout.addSpacing(10)
        
        # 视图切换按钮
        self.list_btn = QPushButton("≡")
        self.list_btn.setToolTip("列表视图")
        self.list_btn.setFixedSize(30, 30)
        self.list_btn.setCheckable(True)
        self.list_btn.setChecked(True)
        self.list_btn.clicked.connect(lambda: self.switch_view('list'))
        layout.addWidget(self.list_btn)
        
        self.grid_btn = QPushButton("⊞")
        self.grid_btn.setToolTip("网格视图")
        self.grid_btn.setFixedSize(30, 30)
        self.grid_btn.setCheckable(True)
        self.grid_btn.clicked.connect(lambda: self.switch_view('grid'))
        layout.addWidget(self.grid_btn)
        
        return bar
    
    def switch_view(self, view_type: str):
        """切换视图"""
        self.current_view = view_type
        
        if view_type == 'list':
            self.stack.setCurrentWidget(self.list_view)
            self.list_btn.setChecked(True)
            self.grid_btn.setChecked(False)
        else:
            self.stack.setCurrentWidget(self.grid_view)
            self.list_btn.setChecked(False)
            self.grid_btn.setChecked(True)
        
        logger.info(f"切换到 {view_type} 视图")
    
    def load_documents(self, documents: list):
        """加载文档"""
        self.documents = documents
        
        # 更新计数
        self.count_label.setText(f"{len(documents)} 个文档")
        
        # 同时更新两个视图
        self.list_view.load_documents(documents)
        self.grid_view.load_documents(documents)
    
    def on_sort_changed(self, index: int):
        """排序变化"""
        if not self.documents:
            return
        
        sort_map = {
            0: ('imported_at', True),
            1: ('imported_at', False),
            2: ('filename', False),
            3: ('filename', True),
            4: ('file_size', True),
            5: ('file_size', False),
        }
        
        key, reverse = sort_map.get(index, ('imported_at', True))
        
        sorted_docs = sorted(
            self.documents,
            key=lambda d: d.get(key, '') or '',
            reverse=reverse
        )
        
        # 更新视图（不重新查询）
        self.list_view.load_documents(sorted_docs)
        self.grid_view.load_documents(sorted_docs)
    
    def get_selected_document_ids(self) -> list:
        """获取选中的文档ID"""
        if self.current_view == 'list':
            return self.list_view.get_selected_document_ids()
        else:
            return self.grid_view.get_selected_document_ids()