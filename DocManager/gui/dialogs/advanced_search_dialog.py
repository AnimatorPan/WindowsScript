"""
高级搜索对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QSpinBox,
    QPushButton, QLabel, QGroupBox, QCheckBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AdvancedSearchDialog(QDialog):
    """高级搜索对话框"""
    
    search_triggered = pyqtSignal(dict)  # 搜索条件信号
    
    def __init__(self, db, library_id, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        
        self.init_ui()
        self.load_options()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("高级搜索")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # 基本条件
        basic_group = QGroupBox("基本条件")
        basic_layout = QFormLayout(basic_group)
        
        # 文件名
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("输入关键词...")
        basic_layout.addRow("文件名包含:", self.filename_edit)
        
        # 文件类型
        self.filetype_combo = QComboBox()
        self.filetype_combo.addItem("全部类型", None)
        basic_layout.addRow("文件类型:", self.filetype_combo)
        
        layout.addWidget(basic_group)
        
        # 分类和标签
        cat_tag_group = QGroupBox("分类与标签")
        cat_tag_layout = QFormLayout(cat_tag_group)
        
        # 分类
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部分类", None)
        cat_tag_layout.addRow("分类:", self.category_combo)
        
        # 标签
        tag_layout = QVBoxLayout()
        self.tag_list = QListWidget()
        self.tag_list.setMaximumHeight(100)
        self.tag_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        tag_layout.addWidget(self.tag_list)
        
        self.tag_match_all = QCheckBox("匹配所有标签（AND）")
        tag_layout.addWidget(self.tag_match_all)
        
        cat_tag_layout.addRow("标签:", tag_layout)
        
        layout.addWidget(cat_tag_group)
        
        # 日期范围
        date_group = QGroupBox("日期范围")
        date_layout = QFormLayout(date_group)
        
        # 日期字段选择
        self.date_field_combo = QComboBox()
        self.date_field_combo.addItems([
            "导入时间",
            "修改时间",
            "创建时间"
        ])
        date_layout.addRow("日期字段:", self.date_field_combo)
        
        # 开始日期
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_check = QCheckBox("启用")
        start_layout = QHBoxLayout()
        start_layout.addWidget(self.start_date)
        start_layout.addWidget(self.start_date_check)
        date_layout.addRow("开始日期:", start_layout)
        
        # 结束日期
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date_check = QCheckBox("启用")
        end_layout = QHBoxLayout()
        end_layout.addWidget(self.end_date)
        end_layout.addWidget(self.end_date_check)
        date_layout.addRow("结束日期:", end_layout)
        
        layout.addWidget(date_group)
        
        # 文件大小
        size_group = QGroupBox("文件大小")
        size_layout = QFormLayout(size_group)
        
        # 最小大小
        min_size_layout = QHBoxLayout()
        self.min_size = QSpinBox()
        self.min_size.setMaximum(99999)
        self.min_size.setSuffix(" KB")
        min_size_layout.addWidget(self.min_size)
        self.min_size_check = QCheckBox("启用")
        min_size_layout.addWidget(self.min_size_check)
        size_layout.addRow("最小大小:", min_size_layout)
        
        # 最大大小
        max_size_layout = QHBoxLayout()
        self.max_size = QSpinBox()
        self.max_size.setMaximum(99999)
        self.max_size.setSuffix(" KB")
        max_size_layout.addWidget(self.max_size)
        self.max_size_check = QCheckBox("启用")
        max_size_layout.addWidget(self.max_size_check)
        size_layout.addRow("最大大小:", max_size_layout)
        
        layout.addWidget(size_group)
        
        # 其他选项
        other_group = QGroupBox("其他条件")
        other_layout = QVBoxLayout(other_group)
        
        self.uncategorized_check = QCheckBox("仅显示未分类文档")
        other_layout.addWidget(self.uncategorized_check)
        
        self.untagged_check = QCheckBox("仅显示未打标签文档")
        other_layout.addWidget(self.untagged_check)
        
        self.duplicate_check = QCheckBox("仅显示重复文档")
        other_layout.addWidget(self.duplicate_check)
        
        layout.addWidget(other_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_form)
        button_layout.addWidget(reset_btn)
        
        search_btn = QPushButton("搜索")
        search_btn.setDefault(True)
        search_btn.clicked.connect(self.do_search)
        button_layout.addWidget(search_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_options(self):
        """加载选项"""
        from core.category import CategoryManager
        from core.tag import TagManager
        
        try:
            # 加载文件类型
            sql = """
                SELECT DISTINCT file_type 
                FROM documents 
                WHERE library_id = ? AND file_type IS NOT NULL
                ORDER BY file_type
            """
            types = self.db.fetch_all(sql, (self.library_id,))
            for t in types:
                file_type = t['file_type']
                self.filetype_combo.addItem(file_type.upper(), file_type)
            
            # 加载分类
            cat_manager = CategoryManager(self.db, self.library_id)
            categories = cat_manager.list_all()
            for cat in categories:
                self.category_combo.addItem(cat['name'], cat['id'])
            
            # 加载标签
            tag_manager = TagManager(self.db, self.library_id)
            tags = tag_manager.list_all()
            for tag in tags:
                item = QListWidgetItem(tag['name'])
                item.setData(Qt.ItemDataRole.UserRole, tag['id'])
                self.tag_list.addItem(item)
        
        except Exception as e:
            logger.error(f"加载选项失败: {e}")
    
    def reset_form(self):
        """重置表单"""
        self.filename_edit.clear()
        self.filetype_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.tag_list.clearSelection()
        self.tag_match_all.setChecked(False)
        
        self.start_date_check.setChecked(False)
        self.end_date_check.setChecked(False)
        self.min_size_check.setChecked(False)
        self.max_size_check.setChecked(False)
        
        self.uncategorized_check.setChecked(False)
        self.untagged_check.setChecked(False)
        self.duplicate_check.setChecked(False)
    
    def do_search(self):
        """执行搜索"""
        filters = {}
        
        # 文件名
        keyword = self.filename_edit.text().strip()
        if keyword:
            filters['keyword'] = keyword
        
        # 文件类型
        file_type = self.filetype_combo.currentData()
        if file_type:
            filters['file_types'] = [file_type]
        
        # 分类
        category_id = self.category_combo.currentData()
        if category_id:
            filters['category_id'] = category_id
        
        # 标签
        selected_tags = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.tag_list.selectedItems()
        ]
        if selected_tags:
            filters['tag_ids'] = selected_tags
            filters['tag_match_all'] = self.tag_match_all.isChecked()
        
        # 日期
        date_field_map = {
            "导入时间": "imported_at",
            "修改时间": "modified_at",
            "创建时间": "created_at"
        }
        date_field = date_field_map[self.date_field_combo.currentText()]
        filters['date_field'] = date_field
        
        if self.start_date_check.isChecked():
            filters['start_date'] = self.start_date.date().toString("yyyy-MM-dd")
        
        if self.end_date_check.isChecked():
            filters['end_date'] = self.end_date.date().toString("yyyy-MM-dd")
        
        # 文件大小
        if self.min_size_check.isChecked():
            filters['min_size'] = self.min_size.value() * 1024  # KB to bytes
        
        if self.max_size_check.isChecked():
            filters['max_size'] = self.max_size.value() * 1024
        
        # 其他条件
        if self.uncategorized_check.isChecked():
            filters['is_uncategorized'] = True
        
        if self.untagged_check.isChecked():
            filters['is_untagged'] = True
        
        if self.duplicate_check.isChecked():
            filters['is_duplicate'] = True
        
        # 发出搜索信号
        self.search_triggered.emit(filters)
        self.accept()