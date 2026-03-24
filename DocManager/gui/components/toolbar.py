"""
工具栏组件（完整版）
"""
from PyQt6.QtWidgets import QToolBar, QLineEdit, QPushButton, QWidget, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction


class Toolbar(QToolBar):
    """工具栏"""
    
    import_clicked = pyqtSignal()
    search_triggered = pyqtSignal(str)
    advanced_search_clicked = pyqtSignal()
    view_list_clicked = pyqtSignal()
    view_grid_clicked = pyqtSignal()
    unorganized_clicked = pyqtSignal()
    statistics_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMovable(False)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 导入按钮
        import_action = QAction("导入文档", self)
        import_action.triggered.connect(self.import_clicked.emit)
        self.addAction(import_action)
        
        self.addSeparator()
        
        # 搜索框
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(5, 0, 5, 0)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索文档...")
        self.search_edit.setMinimumWidth(250)
        self.search_edit.returnPressed.connect(self.on_search)
        search_layout.addWidget(self.search_edit)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(search_btn)
        
        # 高级搜索按钮
        advanced_btn = QPushButton("高级")
        advanced_btn.clicked.connect(self.advanced_search_clicked.emit)
        search_layout.addWidget(advanced_btn)
        
        self.addWidget(search_widget)
        
        self.addSeparator()
        
        # 视图切换
        list_action = QAction("列表视图", self)
        list_action.triggered.connect(self.view_list_clicked.emit)
        self.addAction(list_action)
        
        grid_action = QAction("网格视图", self)
        grid_action.triggered.connect(self.view_grid_clicked.emit)
        self.addAction(grid_action)
        
        self.addSeparator()
        
        # 待整理中心
        unorganized_action = QAction("待整理", self)
        unorganized_action.triggered.connect(self.unorganized_clicked.emit)
        self.addAction(unorganized_action)
        
        # 统计
        statistics_action = QAction("统计", self)
        statistics_action.triggered.connect(self.statistics_clicked.emit)
        self.addAction(statistics_action)
    
    def on_search(self):
        """搜索"""
        keyword = self.search_edit.text().strip()
        if keyword:
            self.search_triggered.emit(keyword)
