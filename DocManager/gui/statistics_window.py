"""
统计报表窗口
"""
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QGridLayout, QLabel, 
    QTabWidget, QTableWidget, QTableWidgetItem,
    QGroupBox, QPushButton
)
from PyQt6.QtCore import Qt
import logging

from core.statistics import StatisticsManager

logger = logging.getLogger(__name__)


class StatisticsWindow(QDialog):
    """统计报表窗口"""
    
    def __init__(self, db, library_id, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        self.stats_manager = StatisticsManager(db, library_id)
        
        self.init_ui()
        self.load_statistics()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("统计报表")
        self.setMinimumSize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("📊 统计报表")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)
        
        # 标签页
        self.tabs = QTabWidget()
        
        # 总览标签页
        overview_tab = self.create_overview_tab()
        self.tabs.addTab(overview_tab, "总览")
        
        # 文件类型标签页
        type_tab = self.create_type_tab()
        self.tabs.addTab(type_tab, "文件类型")
        
        # 分类标签页
        category_tab = self.create_category_tab()
        self.tabs.addTab(category_tab, "分类统计")
        
        # 标签标签页
        tag_tab = self.create_tag_tab()
        self.tabs.addTab(tag_tab, "标签统计")
        
        layout.addWidget(self.tabs)
        
        # 按钮区域
        button_layout = QVBoxLayout()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_statistics)
        button_layout.addWidget(refresh_btn)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_overview_tab(self):
        """创建总览标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 统计卡片
        cards_layout = QGridLayout()
        
        self.total_docs_label = self.create_stat_card("文档总数", "0")
        cards_layout.addWidget(self.total_docs_label, 0, 0)
        
        self.categories_label = self.create_stat_card("分类数", "0", "#4CAF50")
        cards_layout.addWidget(self.categories_label, 0, 1)
        
        self.tags_label = self.create_stat_card("标签数", "0", "#2196F3")
        cards_layout.addWidget(self.tags_label, 1, 0)
        
        self.uncategorized_label = self.create_stat_card("未分类", "0", "#FF9800")
        cards_layout.addWidget(self.uncategorized_label, 1, 1)
        
        self.duplicates_label = self.create_stat_card("重复文档", "0", "#f44336")
        cards_layout.addWidget(self.duplicates_label, 2, 0)
        
        self.storage_size_label = self.create_stat_card("存储空间", "0 B", "#9C27B0")
        cards_layout.addWidget(self.storage_size_label, 2, 1)
        
        layout.addLayout(cards_layout)
        layout.addStretch()
        
        return widget
    
    def create_stat_card(self, title: str, value: str, color: str = "#0d7377"):
        """创建统计卡片"""
        group = QGroupBox()
        group_layout = QVBoxLayout(group)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12pt; color: #888;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24pt; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setObjectName(f"{title}_value")
        group_layout.addWidget(value_label)
        
        return group
    
    def create_type_tab(self):
        """创建文件类型标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.type_table = QTableWidget()
        self.type_table.setColumnCount(3)
        self.type_table.setHorizontalHeaderLabels(["文件类型", "数量", "总大小"])
        self.type_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.type_table)
        
        return widget
    
    def create_category_tab(self):
        """创建分类标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(2)
        self.category_table.setHorizontalHeaderLabels(["分类名称", "文档数量"])
        self.category_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.category_table)
        
        return widget
    
    def create_tag_tab(self):
        """创建标签标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.tag_table = QTableWidget()
        self.tag_table.setColumnCount(2)
        self.tag_table.setHorizontalHeaderLabels(["标签名称", "使用次数"])
        self.tag_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tag_table)
        
        return widget
    
    def load_statistics(self):
        """加载统计数据"""
        try:
            # 获取总览数据
            overview = self.stats_manager.get_overview()
            self.update_overview(overview)
            
            # 获取文件类型数据
            type_data = self.stats_manager.get_type_distribution()
            self.update_type_table(type_data)
            
            # 获取分类数据
            category_data = self.stats_manager.get_category_stats()
            self.update_category_table(category_data)
            
            # 获取标签数据
            tag_data = self.stats_manager.get_tag_stats()
            self.update_tag_table(tag_data)
            
            logger.info("统计数据加载完成")
        
        except Exception as e:
            logger.error(f"加载统计数据失败: {e}")
    
    def update_overview(self, stats: dict):
        """更新总览"""
        # 更新文档总数
        self.total_docs_label.findChild(QLabel, "文档总数_value").setText(
            str(stats.get('total_documents', 0))
        )
        
        # 更新分类数
        self.categories_label.findChild(QLabel, "分类数_value").setText(
            str(stats.get('total_categories', 0))
        )
        
        # 更新标签数
        self.tags_label.findChild(QLabel, "标签数_value").setText(
            str(stats.get('total_tags', 0))
        )
        
        # 更新未分类
        self.uncategorized_label.findChild(QLabel, "未分类_value").setText(
            str(stats.get('uncategorized_documents', 0))
        )
        
        # 更新重复
        self.duplicates_label.findChild(QLabel, "重复文档_value").setText(
            str(stats.get('duplicate_documents', 0))
        )
        
        # 更新存储空间
        self.storage_size_label.findChild(QLabel, "存储空间_value").setText(
            self.format_size(stats.get('total_size', 0))
        )
    
    def update_type_table(self, data: list):
        """更新文件类型表格"""
        self.type_table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.type_table.setItem(row, 0, QTableWidgetItem(item.get('type', '未知').upper()))
            self.type_table.setItem(row, 1, QTableWidgetItem(str(item.get('count', 0))))
            self.type_table.setItem(row, 2, QTableWidgetItem(self.format_size(item.get('size', 0))))
    
    def update_category_table(self, data: list):
        """更新分类表格"""
        self.category_table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.category_table.setItem(row, 0, QTableWidgetItem(item.get('name', '')))
            self.category_table.setItem(row, 1, QTableWidgetItem(str(item.get('count', 0))))
    
    def update_tag_table(self, data: list):
        """更新标签表格"""
        self.tag_table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.tag_table.setItem(row, 0, QTableWidgetItem(item.get('name', '')))
            self.tag_table.setItem(row, 1, QTableWidgetItem(str(item.get('count', 0))))
    
    def format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
