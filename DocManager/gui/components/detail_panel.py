"""
详情面板组件（完整版）
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QGroupBox,
    QPushButton, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging
import os
import platform
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class DetailPanel(QWidget):
    """详情面板"""
    
    document_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_window = parent
        self.current_document = None
        self.current_document_id = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("文档详情")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 文件名
        self.filename_label = QLabel("-")
        self.filename_label.setWordWrap(True)
        self.filename_label.setStyleSheet("font-size: 12px; padding: 5px;")
        layout.addWidget(self.filename_label)
        
        # 添加标签页
        from PyQt6.QtWidgets import QTabWidget
        
        self.tabs = QTabWidget()
        
        # 信息标签页
        info_widget = self.create_info_tab()
        self.tabs.addTab(info_widget, "信息")
        
        # 预览标签页
        preview_widget = self.create_preview_tab()
        self.tabs.addTab(preview_widget, "预览")
        
        layout.addWidget(self.tabs)
    
    def create_info_tab(self):
        """创建信息标签页"""
        from PyQt6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout,
            QGroupBox, QPushButton
        )

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ── 操作按钮区 ──────────────────────────────
        action_layout = QHBoxLayout()
        action_layout.setSpacing(5)

        open_btn = QPushButton("📂 打开")
        open_btn.setToolTip("用默认程序打开文件")
        open_btn.clicked.connect(self.open_file)
        action_layout.addWidget(open_btn)

        reveal_btn = QPushButton("📁 定位")
        reveal_btn.setToolTip("在文件夹中显示文件")
        reveal_btn.clicked.connect(self.reveal_in_explorer)
        action_layout.addWidget(reveal_btn)

        copy_btn = QPushButton("📋 复制路径")
        copy_btn.setToolTip("复制文件完整路径")
        copy_btn.clicked.connect(self.copy_path)
        action_layout.addWidget(copy_btn)

        version_btn = QPushButton("🕐 版本")
        version_btn.setToolTip("查看版本历史")
        version_btn.clicked.connect(self.show_versions)
        action_layout.addWidget(version_btn)

        layout.addLayout(action_layout)

        # ── 基本信息 ──────────────────────────────
        info_group = QGroupBox("基本信息")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        info_layout.addWidget(self.info_text)

        layout.addWidget(info_group)

        # ── 分类 ──────────────────────────────────
        category_group = QGroupBox("分类")
        category_layout = QVBoxLayout(category_group)

        self.category_list = QListWidget()
        self.category_list.setMaximumHeight(80)
        category_layout.addWidget(self.category_list)

        cat_btn_layout = QHBoxLayout()
        add_cat_btn = QPushButton("+ 添加")
        add_cat_btn.clicked.connect(self.add_category)
        cat_btn_layout.addWidget(add_cat_btn)

        remove_cat_btn = QPushButton("- 移除")
        remove_cat_btn.clicked.connect(self.remove_category)
        cat_btn_layout.addWidget(remove_cat_btn)
        cat_btn_layout.addStretch()

        category_layout.addLayout(cat_btn_layout)
        layout.addWidget(category_group)

        # ── 标签 ──────────────────────────────────
        tag_group = QGroupBox("标签")
        tag_layout = QVBoxLayout(tag_group)

        self.tag_list = QListWidget()
        self.tag_list.setMaximumHeight(80)
        tag_layout.addWidget(self.tag_list)

        tag_btn_layout = QHBoxLayout()
        add_tag_btn = QPushButton("+ 添加")
        add_tag_btn.clicked.connect(self.add_tag)
        tag_btn_layout.addWidget(add_tag_btn)

        remove_tag_btn = QPushButton("- 移除")
        remove_tag_btn.clicked.connect(self.remove_tag)
        tag_btn_layout.addWidget(remove_tag_btn)
        tag_btn_layout.addStretch()

        tag_layout.addLayout(tag_btn_layout)
        layout.addWidget(tag_group)

        # ── 备注 ──────────────────────────────────
        note_group = QGroupBox("备注")
        note_layout = QVBoxLayout(note_group)

        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(70)
        self.note_edit.setPlaceholderText("添加备注...")
        note_layout.addWidget(self.note_edit)

        save_note_btn = QPushButton("💾 保存备注")
        save_note_btn.clicked.connect(self.save_note)
        note_layout.addWidget(save_note_btn)

        layout.addWidget(note_group)
        layout.addStretch()

        return widget

    def open_file(self):
        """打开文件"""
        if not self.current_document:
            return

        import os, platform
        from pathlib import Path

        try:
            storage_path = Path(self.main_window.current_library['storage_path'])
            file_path = storage_path / self.current_document['filepath']

            if not file_path.exists():
                QMessageBox.warning(self, "错误", f"文件不存在:\n{file_path}")
                return

            if platform.system() == 'Windows':
                os.startfile(str(file_path))
            elif platform.system() == 'Darwin':
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')

        except Exception as e:
            logger.error(f"打开文件失败: {e}")
            QMessageBox.critical(self, "错误", f"打开失败:\n{e}")

    def reveal_in_explorer(self):
        """在文件夹中显示"""
        if not self.current_document:
            return

        import subprocess, platform
        from pathlib import Path

        try:
            storage_path = Path(self.main_window.current_library['storage_path'])
            file_path = storage_path / self.current_document['filepath']

            if not file_path.exists():
                QMessageBox.warning(self, "错误", f"文件不存在:\n{file_path}")
                return

            if platform.system() == 'Windows':
                subprocess.run(f'explorer /select,"{file_path}"', shell=True)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', '-R', str(file_path)])
            else:
                subprocess.run(['xdg-open', str(file_path.parent)])

        except Exception as e:
            logger.error(f"定位文件失败: {e}")
            QMessageBox.critical(self, "错误", f"定位失败:\n{e}")

    def copy_path(self):
        """复制文件路径"""
        if not self.current_document:
            return

        from PyQt6.QtWidgets import QApplication
        from pathlib import Path

        try:
            storage_path = Path(self.main_window.current_library['storage_path'])
            file_path = storage_path / self.current_document['filepath']

            QApplication.clipboard().setText(str(file_path))
            # 短暂提示
            self.main_window.status_bar.show_message("路径已复制到剪贴板", 2000)

        except Exception as e:
            logger.error(f"复制路径失败: {e}")

    def show_versions(self):
        """显示版本管理"""
        if not self.current_document_id:
            return

        from gui.version_manager_window import VersionManagerWindow

        window = VersionManagerWindow(
            self.main_window.db,
            self.main_window.library_id,
            self.current_document_id,
            self
        )
        window.show()
    
    def create_preview_tab(self):
        """创建预览标签页"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 预览区域（初始为空）
        self.preview_container = QVBoxLayout()
        self.preview_widget = None
        
        self.no_preview_label = QLabel("选择文档查看预览")
        self.no_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_container.addWidget(self.no_preview_label)
        
        layout.addLayout(self.preview_container)
        
        return widget
    
    def load_document(self, document_id: int):
        """加载文档详情"""
        self.current_document_id = document_id
        
        if not self.main_window.db or not document_id:
            return
        
        try:
            from core.document import DocumentManager
            
            doc_manager = DocumentManager(self.main_window.db, self.main_window.library_id)
            self.current_document = doc_manager.get(document_id)
            
            if self.current_document:
                # 更新文件名
                self.filename_label.setText(self.current_document['filename'])
                
                # 更新基本信息
                info_text = f"""文件名: {self.current_document['filename']}
类型: {self.current_document['file_type'] or '未知'}
大小: {self.current_document['file_size'] or 0} bytes
路径: {self.current_document['filepath']}
导入时间: {self.current_document.get('imported_at', '')}"""
                self.info_text.setText(info_text)
                
                # 加载分类和标签
                self.load_categories()
                self.load_tags()
                
                # 加载备注
                self.note_edit.setText(self.current_document.get('note', ''))
                
                # 加载预览
                self.load_preview()
                
                logger.info(f"加载文档详情: {self.current_document['filename']}")
        
        except Exception as e:
            logger.error(f"加载文档详情失败: {e}")
    
    def load_categories(self):
        """加载分类列表"""
        self.category_list.clear()
        
        if not self.current_document:
            return
        
        try:
            from core.document import DocumentManager
            
            doc_manager = DocumentManager(self.main_window.db, self.main_window.library_id)
            categories = doc_manager.get_categories(self.current_document_id)
            
            for cat in categories:
                item = QListWidgetItem(cat['name'])
                item.setData(Qt.ItemDataRole.UserRole, cat['id'])
                self.category_list.addItem(item)
        
        except Exception as e:
            logger.error(f"加载分类失败: {e}")
    
    def load_tags(self):
        """加载标签列表"""
        self.tag_list.clear()
        
        if not self.current_document:
            return
        
        try:
            from core.document import DocumentManager
            
            doc_manager = DocumentManager(self.main_window.db, self.main_window.library_id)
            tags = doc_manager.get_tags(self.current_document_id)
            
            for tag in tags:
                item = QListWidgetItem(tag['name'])
                item.setData(Qt.ItemDataRole.UserRole, tag['id'])
                self.tag_list.addItem(item)
        
        except Exception as e:
            logger.error(f"加载标签失败: {e}")
    
    def load_preview(self):
        """加载文档预览"""
        if not self.current_document:
            return
        
        try:
            # 构建完整路径
            storage_path = Path(self.main_window.current_library['storage_path'])
            file_path = storage_path / self.current_document['filepath']
            
            if not file_path.exists():
                self.show_no_preview("文件不存在")
                return
            
            # 清除旧预览
            if self.preview_widget:
                self.preview_container.removeWidget(self.preview_widget)
                self.preview_widget.deleteLater()
                self.preview_widget = None
            
            if self.no_preview_label:
                self.preview_container.removeWidget(self.no_preview_label)
                self.no_preview_label.deleteLater()
                self.no_preview_label = None
            
            # 使用 PreviewFactory 创建预览组件
            from .preview_factory import PreviewFactory
            
            self.preview_widget = PreviewFactory.create_preview(str(file_path), self)
            self.preview_widget.preview(str(file_path))
            self.preview_container.addWidget(self.preview_widget)
            
            logger.info(f"加载预览: {file_path}")
        
        except Exception as e:
            logger.error(f"加载预览失败: {e}")
            self.show_no_preview(f"预览失败: {str(e)}")
    
    def show_no_preview(self, message: str):
        """显示无预览消息"""
        if self.preview_widget:
            self.preview_container.removeWidget(self.preview_widget)
            self.preview_widget.deleteLater()
            self.preview_widget = None
        
        if not self.no_preview_label:
            self.no_preview_label = QLabel()
            self.no_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_container.addWidget(self.no_preview_label)
        
        self.no_preview_label.setText(message)
    
    def add_category(self):
        """添加分类"""
        if not self.current_document_id:
            QMessageBox.warning(self, "提示", "请先选择文档")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        from core.category import CategoryManager
        from core.document import DocumentManager
        
        try:
            cat_manager = CategoryManager(self.main_window.db, self.main_window.library_id)
            doc_manager = DocumentManager(self.main_window.db, self.main_window.library_id)
            all_categories = cat_manager.list_all()
            
            if not all_categories:
                QMessageBox.warning(self, "提示", "没有可用的分类，请先创建分类")
                return
            
            # 获取当前文档已有的分类
            current_cats = doc_manager.get_categories(self.current_document_id)
            current_cat_ids = {c['id'] for c in current_cats}
            
            # 过滤出可选的分类
            available_cats = [c for c in all_categories if c['id'] not in current_cat_ids]
            
            if not available_cats:
                QMessageBox.information(self, "提示", "该文档已关联所有分类")
                return
            
            # 显示选择对话框
            cat_names = [c['name'] for c in available_cats]
            name, ok = QInputDialog.getItem(
                self, "添加分类", "选择分类:", cat_names, 0, False
            )
            
            if ok and name:
                # 找到选中的分类
                selected_cat = next((c for c in available_cats if c['name'] == name), None)
                if selected_cat:
                    cat_manager.add_document(selected_cat['id'], self.current_document_id)
                    self.load_categories()
                    self.document_updated.emit()
                    QMessageBox.information(self, "成功", f"已添加到分类: {name}")
        
        except Exception as e:
            logger.error(f"添加分类失败: {e}")
            QMessageBox.critical(self, "错误", f"添加分类失败: {str(e)}")
    
    def remove_category(self):
        """移除分类"""
        if not self.current_document_id:
            return
        
        current_item = self.category_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要移除的分类")
            return
        
        cat_id = current_item.data(Qt.ItemDataRole.UserRole)
        cat_name = current_item.text()
        
        reply = QMessageBox.question(
            self, "确认移除",
            f"确定要将文档从分类 '{cat_name}' 中移除吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.category import CategoryManager
                cat_manager = CategoryManager(self.main_window.db, self.main_window.library_id)
                cat_manager.remove_document(cat_id, self.current_document_id)
                self.load_categories()
                self.document_updated.emit()
                QMessageBox.information(self, "成功", "已移除分类")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"移除失败: {str(e)}")
    
    def add_tag(self):
        """添加标签"""
        if not self.current_document_id:
            QMessageBox.warning(self, "提示", "请先选择文档")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        from core.tag import TagManager
        from core.document import DocumentManager
        
        try:
            tag_manager = TagManager(self.main_window.db, self.main_window.library_id)
            doc_manager = DocumentManager(self.main_window.db, self.main_window.library_id)
            all_tags = tag_manager.list_all()
            
            if not all_tags:
                # 提供创建新标签的选项
                name, ok = QInputDialog.getText(self, "创建标签", "输入新标签名称:")
                if ok and name.strip():
                    tag_manager.create(name.strip())
                    self.load_tags()
                    self.document_updated.emit()
                    QMessageBox.information(self, "成功", f"已创建标签: {name}")
                return
            
            # 获取当前文档已有的标签
            current_tags = doc_manager.get_tags(self.current_document_id)
            current_tag_ids = {t['id'] for t in current_tags}
            
            # 过滤出可选的标签
            available_tags = [t for t in all_tags if t['id'] not in current_tag_ids]
            
            if not available_tags:
                # 提供创建新标签的选项
                name, ok = QInputDialog.getText(self, "创建标签", "输入新标签名称:")
                if ok and name.strip():
                    tag_manager.create(name.strip())
                    self.load_tags()
                    self.document_updated.emit()
                    QMessageBox.information(self, "成功", f"已创建标签: {name}")
                return
            
            # 显示选择对话框
            tag_names = [t['name'] for t in available_tags] + ["[创建新标签]"]
            name, ok = QInputDialog.getItem(
                self, "添加标签", "选择标签:", tag_names, 0, False
            )
            
            if ok and name:
                if name == "[创建新标签]":
                    new_name, ok2 = QInputDialog.getText(self, "创建标签", "输入新标签名称:")
                    if ok2 and new_name.strip():
                        tag_manager.create(new_name.strip())
                        self.load_tags()
                        self.document_updated.emit()
                        QMessageBox.information(self, "成功", f"已创建标签: {new_name}")
                else:
                    # 找到选中的标签
                    selected_tag = next((t for t in available_tags if t['name'] == name), None)
                    if selected_tag:
                        tag_manager.add_to_document(selected_tag['id'], self.current_document_id)
                        self.load_tags()
                        self.document_updated.emit()
                        QMessageBox.information(self, "成功", f"已添加标签: {name}")
        
        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            QMessageBox.critical(self, "错误", f"添加标签失败: {str(e)}")
    
    def remove_tag(self):
        """移除标签"""
        if not self.current_document_id:
            return
        
        current_item = self.tag_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要移除的标签")
            return
        
        tag_id = current_item.data(Qt.ItemDataRole.UserRole)
        tag_name = current_item.text()
        
        reply = QMessageBox.question(
            self, "确认移除",
            f"确定要移除标签 '{tag_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.tag import TagManager
                tag_manager = TagManager(self.main_window.db, self.main_window.library_id)
                tag_manager.remove_from_document(tag_id, self.current_document_id)
                self.load_tags()
                self.document_updated.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"移除失败: {str(e)}")
    
    def save_note(self):
        """保存备注"""
        if not self.current_document_id:
            return
        
        try:
            from core.document import DocumentManager
            
            doc_manager = DocumentManager(self.main_window.db, self.main_window.library_id)
            doc_manager.update(self.current_document_id, note=self.note_edit.toPlainText())
            
            QMessageBox.information(self, "成功", "备注已保存")
            self.document_updated.emit()
        
        except Exception as e:
            logger.error(f"保存备注失败: {e}")
            QMessageBox.critical(self, "错误", f"保存备注失败: {str(e)}")
    
    def clear(self):
        """清空详情"""
        self.current_document = None
        self.current_document_id = None
        self.filename_label.setText("-")
        self.info_text.clear()
        self.category_list.clear()
        self.tag_list.clear()
        self.note_edit.clear()
        self.show_no_preview("选择文档查看预览")
    
    def open_file(self):
        """打开文件"""
        if not self.current_document or not self.main_window.current_library:
            return
        try:
            storage_path = Path(self.main_window.current_library['storage_path'])
            file_path = storage_path / self.current_document['filepath']

            if not file_path.exists():
                QMessageBox.warning(self, "错误", f"文件不存在:\n{file_path}")
                return

            if platform.system() == 'Windows':
                os.startfile(str(file_path))
            elif platform.system() == 'Darwin':
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            logger.error(f"打开文件失败: {e}")
            QMessageBox.critical(self, "错误", f"打开失败:\n{e}")

    def reveal_in_explorer(self):
        """在文件夹中显示"""
        if not self.current_document or not self.main_window.current_library:
            return
        try:
            storage_path = Path(self.main_window.current_library['storage_path'])
            file_path = storage_path / self.current_document['filepath']

            if not file_path.exists():
                QMessageBox.warning(self, "错误", f"文件不存在:\n{file_path}")
                return

            if platform.system() == 'Windows':
                subprocess.run(f'explorer /select,"{file_path}"', shell=True)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', '-R', str(file_path)])
            else:
                subprocess.run(['xdg-open', str(file_path.parent)])
        except Exception as e:
            logger.error(f"定位文件失败: {e}")
            QMessageBox.critical(self, "错误", f"定位失败:\n{e}")

    def copy_path(self):
        """复制文件路径"""
        if not self.current_document or not self.main_window.current_library:
            return
        try:
            from PyQt6.QtWidgets import QApplication
            storage_path = Path(self.main_window.current_library['storage_path'])
            file_path = storage_path / self.current_document['filepath']
            QApplication.clipboard().setText(str(file_path))
            self.main_window.status_bar.show_message("路径已复制到剪贴板", 2000)
        except Exception as e:
            logger.error(f"复制路径失败: {e}")

    def show_versions(self):
        """显示版本管理"""
        if not self.current_document_id:
            return
        from gui.version_manager_window import VersionManagerWindow
        window = VersionManagerWindow(
            self.main_window.db,
            self.main_window.library_id,
            self.current_document_id,
            self
        )
        window.show()

    def load_preview(self):
        """加载文档预览"""
        if not self.current_document or not self.main_window.current_library:
            return
        try:
            from gui.components.preview_factory import PreviewFactory
            storage_path = Path(self.main_window.current_library['storage_path'])
            file_path = storage_path / self.current_document['filepath']

            if not file_path.exists():
                self.show_no_preview("文件不存在")
                return

            if not PreviewFactory.is_previewable(str(file_path)):
                self.show_no_preview("该文件类型暂不支持预览")
                return

            # 清除旧预览
            while self.preview_container.count():
                item = self.preview_container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # 创建新预览
            self.preview_widget = PreviewFactory.create_preview(str(file_path))
            self.preview_container.addWidget(self.preview_widget)
            self.preview_widget.load_file(str(file_path))

        except Exception as e:
            logger.error(f"加载预览失败: {e}")
            self.show_no_preview(f"预览失败: {e}")

    def show_no_preview(self, message: str):
        """显示无预览消息"""
        while self.preview_container.count():
            item = self.preview_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888;")
        self.preview_container.addWidget(label)