"""
版本管理窗口
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox,
    QInputDialog
)
from PyQt6.QtCore import Qt
import logging

from core.version_manager import VersionManager

logger = logging.getLogger(__name__)


class VersionManagerWindow(QWidget):
    """版本管理窗口"""
    
    def __init__(self, db, library_id, document_id, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        self.document_id = document_id
        self.version_manager = VersionManager(db, library_id)
        
        self.init_ui()
        self.load_versions()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("版本管理")
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("📝 版本历史")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 版本表格
        self.version_table = QTableWidget()
        self.version_table.setColumnCount(5)
        self.version_table.setHorizontalHeaderLabels([
            "版本号", "状态", "创建时间", "说明", "创建人"
        ])
        layout.addWidget(self.version_table)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加新版本")
        add_btn.clicked.connect(self.add_version)
        button_layout.addWidget(add_btn)
        
        set_current_btn = QPushButton("设为当前版本")
        set_current_btn.clicked.connect(self.set_current)
        button_layout.addWidget(set_current_btn)
        
        delete_btn = QPushButton("删除版本")
        delete_btn.clicked.connect(self.delete_version)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_versions)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
    
    def load_versions(self):
        """加载版本列表"""
        try:
            versions = self.version_manager.get_versions(self.document_id)
            
            self.version_table.setRowCount(len(versions))
            
            for row, version in enumerate(versions):
                # 版本号
                self.version_table.setItem(
                    row, 0,
                    QTableWidgetItem(str(version['version_number']))
                )
                
                # 状态
                status = "当前版本" if version['is_current'] else ""
                self.version_table.setItem(row, 1, QTableWidgetItem(status))
                
                # 创建时间
                self.version_table.setItem(
                    row, 2,
                    QTableWidgetItem(version.get('created_at', ''))
                )
                
                # 说明
                self.version_table.setItem(
                    row, 3,
                    QTableWidgetItem(version.get('version_note', ''))
                )
                
                # 创建人
                self.version_table.setItem(
                    row, 4,
                    QTableWidgetItem(version.get('created_by', ''))
                )
                
                # 存储版本ID
                self.version_table.item(row, 0).setData(
                    Qt.ItemDataRole.UserRole, version['id']
                )
            
            logger.info(f"加载版本列表: {len(versions)} 个版本")
        
        except Exception as e:
            logger.error(f"加载版本列表失败: {e}")
            QMessageBox
        except Exception as e:
            logger.error(f"加载版本列表失败: {e}")
            QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")
    
    def add_version(self):
        """添加新版本"""
        note, ok = QInputDialog.getText(self, "添加版本", "版本说明:")
        
        if ok:
            try:
                # 获取当前最大版本号
                versions = self.version_manager.get_versions(self.document_id)
                max_version = max([v['version_number'] for v in versions], default=0)
                
                self.version_manager.create_version(
                    self.document_id,
                    version_number=max_version + 1,
                    is_current=True,
                    note=note
                )
                
                self.load_versions()
                QMessageBox.information(self, "成功", "版本添加成功")
            
            except Exception as e:
                logger.error(f"添加版本失败: {e}")
                QMessageBox.critical(self, "错误", f"添加失败: {str(e)}")
    
    def set_current(self):
        """设为当前版本"""
        selected_rows = self.version_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请选择要设置的版本")
            return
        
        row = selected_rows[0].row()
        version_id = self.version_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        try:
            self.version_manager.set_current_version(version_id)
            self.load_versions()
            QMessageBox.information(self, "成功", "已设置为当前版本")
        
        except Exception as e:
            logger.error(f"设置当前版本失败: {e}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")
    
    def delete_version(self):
        """删除版本"""
        selected_rows = self.version_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请选择要删除的版本")
            return
        
        row = selected_rows[0].row()
        version_id = self.version_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除此版本吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.version_manager.delete_version(version_id)
                self.load_versions()
                QMessageBox.information(self, "成功", "版本删除成功")
            
            except ValueError as e:
                QMessageBox.warning(self, "提示", str(e))
            
            except Exception as e:
                logger.error(f"删除版本失败: {e}")
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")