"""
标签管理对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QLabel,
    QMessageBox, QInputDialog, QColorDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import logging

from core.tag import TagManager

logger = logging.getLogger(__name__)


class TagDialog(QDialog):
    """标签管理对话框"""
    
    def __init__(self, db, library_id, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        self.tag_manager = TagManager(db, library_id)
        
        self.init_ui()
        self.load_tags()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("标签管理")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加标签")
        add_btn.clicked.connect(self.add_tag)
        toolbar_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_tag)
        toolbar_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_tag)
        toolbar_layout.addWidget(delete_btn)
        
        merge_btn = QPushButton("合并标签")
        merge_btn.clicked.connect(self.merge_tags)
        toolbar_layout.addWidget(merge_btn)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 标签树
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["标签名称", "使用次数", "颜色"])
        self.tree.setColumnWidth(0, 250)
        layout.addWidget(self.tree)
        
        # 统计信息
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_tags(self):
        """加载标签"""
        self.tree.clear()
        
        try:
            # 获取热门标签
            popular_tags = self.tag_manager.get_popular_tags(limit=100)
            
            for tag in popular_tags:
                if tag['parent_id'] is None:
                    item = QTreeWidgetItem(self.tree)
                    item.setText(0, tag['name'])
                    item.setText(1, str(tag['usage_count']))
                    item.setText(2, tag.get('color', ''))
                    item.setData(0, Qt.ItemDataRole.UserRole, tag['id'])
                    
                    # 设置颜色显示
                    if tag.get('color'):
                        item.setBackground(2, QColor(tag['color']))
            
            self.tree.expandAll()
            
            # 更新统计
            total = len(popular_tags)
            unused = len(self.tag_manager.get_unused_tags())
            self.stats_label.setText(f"总标签: {total} | 未使用: {unused}")
        
        except Exception as e:
            logger.error(f"加载标签失败: {e}")
            QMessageBox.critical(self, "错误", f"加载标签失败: {str(e)}")
    
    def add_tag(self):
        """添加标签"""
        name, ok = QInputDialog.getText(self, "添加标签", "标签名称:")
        
        if ok and name:
            # 选择颜色
            color = QColorDialog.getColor()
            color_hex = color.name() if color.isValid() else None
            
            try:
                self.tag_manager.create(name, color=color_hex)
                self.load_tags()
                QMessageBox.information(self, "成功", "标签创建成功")
            except Exception as e:
                logger.error(f"创建标签失败: {e}")
                QMessageBox.critical(self, "错误", f"创建标签失败: {str(e)}")
    
    def edit_tag(self):
        """编辑标签"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要编辑的标签")
            return
        
        tag_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        old_name = current_item.text(0)
        
        name, ok = QInputDialog.getText(self, "编辑标签", "标签名称:", text=old_name)
        
        if ok and name:
            # 选择颜色
            color = QColorDialog.getColor()
            color_hex = color.name() if color.isValid() else None
            
            try:
                self.tag_manager.update(tag_id, name=name, color=color_hex)
                self.load_tags()
                QMessageBox.information(self, "成功", "标签更新成功")
            except Exception as e:
                logger.error(f"更新标签失败: {e}")
                QMessageBox.critical(self, "错误", f"更新标签失败: {str(e)}")
    
    def delete_tag(self):
        """删除标签"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要删除的标签")
            return
        
        tag_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        tag_name = current_item.text(0)
        usage_count = int(current_item.text(1))
        
        if usage_count > 0:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"标签 '{tag_name}' 正在被 {usage_count} 个文档使用。\n\n"
                "确定要删除吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除标签 '{tag_name}' 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.tag_manager.delete(tag_id)
                self.load_tags()
                QMessageBox.information(self, "成功", "标签删除成功")
            except Exception as e:
                logger.error(f"删除标签失败: {e}")
                QMessageBox.critical(self, "错误", f"删除标签失败: {str(e)}")
    
    def merge_tags(self):
        """合并标签"""
        QMessageBox.information(
            self,
            "提示",
            "合并标签功能：\n\n"
            "1. 选择两个标签\n"
            "2. 第一个标签的文档将合并到第二个标签\n"
            "3. 第一个标签将被删除\n\n"
            "此功能待完善..."
        )