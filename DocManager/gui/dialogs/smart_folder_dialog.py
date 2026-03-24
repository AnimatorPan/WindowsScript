"""
智能文件夹编辑对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QComboBox, QListWidget, QListWidgetItem,
    QMessageBox, QSpinBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
import json
import logging

from core.smart_folder import SmartFolderManager

logger = logging.getLogger(__name__)


class SmartFolderDialog(QDialog):
    """智能文件夹编辑对话框"""
    
    def __init__(self, db, library_id, folder_id=None, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        self.folder_id = folder_id
        self.sf_manager = SmartFolderManager(db, library_id)
        
        self.conditions = []
        
        self.init_ui()
        
        if folder_id:
            self.load_folder()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("智能文件夹" if not self.folder_id else "编辑智能文件夹")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如: 最近导入的PDF")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 规则操作符
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel("规则匹配:"))
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["满足所有条件 (AND)", "满足任一条件 (OR)"])
        operator_layout.addWidget(self.operator_combo)
        operator_layout.addStretch()
        layout.addLayout(operator_layout)
        
        # 条件列表
        layout.addWidget(QLabel("规则条件:"))
        self.condition_list = QListWidget()
        layout.addWidget(self.condition_list)
        
        # 添加条件按钮
        add_condition_layout = QHBoxLayout()
        
        add_type_btn = QPushButton("按文件类型")
        add_type_btn.clicked.connect(lambda: self.add_condition('file_type'))
        add_condition_layout.addWidget(add_type_btn)
        
        add_name_btn = QPushButton("按文件名")
        add_name_btn.clicked.connect(lambda: self.add_condition('filename'))
        add_condition_layout.addWidget(add_name_btn)
        
        add_date_btn = QPushButton("按日期")
        add_date_btn.clicked.connect(lambda: self.add_condition('date'))
        add_condition_layout.addWidget(add_date_btn)
        
        add_uncat_btn = QPushButton("未分类")
        add_uncat_btn.clicked.connect(lambda: self.add_condition('uncategorized'))
        add_condition_layout.addWidget(add_uncat_btn)
        
        layout.addLayout(add_condition_layout)
        
        # 预览
        preview_btn = QPushButton("预览匹配结果")
        preview_btn.clicked.connect(self.preview_matches)
        layout.addWidget(preview_btn)
        
        self.match_label = QLabel("匹配: 0 个文档")
        layout.addWidget(self.match_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_folder)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_folder(self):
        """加载已有智能文件夹"""
        try:
            folder = self.sf_manager.get(self.folder_id)
            if folder:
                self.name_edit.setText(folder['name'])
                
                rules = folder['rules']
                operator = rules.get('operator', 'AND')
                self.operator_combo.setCurrentIndex(0 if operator == 'AND' else 1)
                
                self.conditions = rules.get('conditions', [])
                self.refresh_condition_list()
        
        except Exception as e:
            logger.error(f"加载智能文件夹失败: {e}")
    
    def add_condition(self, condition_type):
        """添加条件"""
        if condition_type == 'file_type':
            from PyQt6.QtWidgets import QInputDialog
            types, ok = QInputDialog.getText(
                self,
                "文件类型",
                "输入文件类型（用逗号分隔）:\n例如: pdf,docx,txt"
            )
            if ok and types:
                type_list = [t.strip() for t in types.split(',')]
                self.conditions.append({
                    'type': 'file_type',
                    'operator': 'in',
                    'value': type_list
                })
        
        elif condition_type == 'filename':
            from PyQt6.QtWidgets import QInputDialog
            keyword, ok = QInputDialog.getText(
                self,
                "文件名",
                "输入关键词:"
            )
            if ok and keyword:
                self.conditions.append({
                    'type': 'filename',
                    'operator': 'contains',
                    'value': keyword
                })
        
        elif condition_type == 'date':
            from PyQt6.QtWidgets import QInputDialog
            days, ok = QInputDialog.getInt(
                self,
                "日期",
                "最近几天导入:",
                7, 1, 365
            )
            if ok:
                self.conditions.append({
                    'type': 'imported_date',
                    'operator': 'within_days',
                    'value': days
                })
        
        elif condition_type == 'uncategorized':
            self.conditions.append({
                'type': 'is_uncategorized',
                'operator': 'equals',
                'value': True
            })
        
        self.refresh_condition_list()
    
    def refresh_condition_list(self):
        """刷新条件列表"""
        self.condition_list.clear()
        
        for i, condition in enumerate(self.conditions):
            text = self.format_condition(condition)
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.condition_list.addItem(item)
    
    def format_condition(self, condition):
        """格式化条件显示"""
        cond_type = condition.get('type')
        value = condition.get('value')
        
        if cond_type == 'file_type':
            return f"文件类型: {', '.join(value)}"
        elif cond_type == 'filename':
            return f"文件名包含: {value}"
        elif cond_type == 'imported_date':
            return f"最近 {value} 天导入"
        elif cond_type == 'is_uncategorized':
            return "未分类文档"
        else:
            return str(condition)
    
    def preview_matches(self):
        """预览匹配结果"""
        rules = self.build_rules()
        
        # 创建临时智能文件夹
        try:
            temp_id = self.sf_manager.create("__temp__", rules)
            count = self.sf_manager.count_matches(temp_id)
            self.sf_manager.delete(temp_id)
            
            self.match_label.setText(f"匹配: {count} 个文档")
        
        except Exception as e:
            logger.error(f"预览失败: {e}")
            self.match_label.setText(f"预览失败: {str(e)}")
    
    def build_rules(self):
        """构建规则"""
        operator = 'AND' if self.operator_combo.currentIndex() == 0 else 'OR'
        
        return {
            'operator': operator,
            'conditions': self.conditions
        }
    
    def save_folder(self):
        """保存智能文件夹"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "提示", "请输入名称")
            return
        
        if not self.conditions:
            QMessageBox.warning(self, "提示", "请至少添加一个条件")
            return
        
        rules = self.build_rules()
        
        try:
            if self.folder_id:
                # 更新
                self.sf_manager.update(self.folder_id, name=name, rules=rules)
                QMessageBox.information(self, "成功", "智能文件夹更新成功")
            else:
                # 创建
                self.sf_manager.create(name, rules)
                QMessageBox.information(self, "成功", "智能文件夹创建成功")
            
            self.accept()
        
        except Exception as e:
            logger.error(f"保存智能文件夹失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")