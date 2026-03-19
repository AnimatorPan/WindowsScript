"""
欢迎对话框 - Visual Studio 2019 Dark 主题
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QLineEdit,
    QTextEdit, QMessageBox, QWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# 修复导入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.library import LibraryManager, LibraryInfo
from gui.styles.app_styles import (
    COLORS, PRIMARY_BUTTON_STYLE, DEFAULT_BUTTON_STYLE, 
    LINE_EDIT_STYLE, TEXT_EDIT_STYLE, LIST_WIDGET_STYLE
)


def get_last_opened_path() -> Optional[str]:
    """获取上次打开的路径（模块级函数）"""
    config_path = os.path.join(Path.home(), '.docmanager', 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('last_opened_path')
        except Exception:
            pass
    return None


def save_last_opened_path(path: str):
    """保存上次打开的路径（模块级函数）"""
    config_dir = os.path.join(Path.home(), '.docmanager')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'config.json')
    
    try:
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        config['last_opened_path'] = path
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DEBUG] 保存配置失败: {e}")


class LibraryListItem(QWidget):
    """自定义库列表项 - VS2019 Dark风格"""
    
    def __init__(self, library: LibraryInfo, parent=None):
        super().__init__(parent)
        self.library = library
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        
        # 库名称
        name_label = QLabel(self.library.name)
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f'color: {COLORS["text_highlight"]};')
        layout.addWidget(name_label)
        
        # 路径
        path_label = QLabel(self.library.path)
        path_font = QFont()
        path_font.setPointSize(10)
        path_label.setFont(path_font)
        path_label.setStyleSheet(f'color: {COLORS["text_secondary"]};')
        path_label.setWordWrap(True)
        layout.addWidget(path_label)


class CreateLibraryDialog(QDialog):
    """创建新库对话框 - VS2019 Dark风格"""
    
    library_created = pyqtSignal(LibraryInfo)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('创建新库')
        self.setMinimumWidth(520)
        self.setModal(True)
        self.selected_path = ''
        self.setup_ui()
        self.apply_styles()
    
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet(f'''
            QDialog {{
                background-color: {COLORS['bg_primary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
        ''')
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # 标题
        title = QLabel('📁 创建新文档库')
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f'color: {COLORS["text_highlight"]};')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 副标题
        subtitle = QLabel('选择一个空文件夹作为文档库的存储位置')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f'color: {COLORS["text_secondary"]}; font-size: 13px; padding-bottom: 8px;')
        layout.addWidget(subtitle)
        
        layout.addSpacing(8)
        
        # 表单区域
        form_frame = QFrame()
        form_frame.setStyleSheet(f'''
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        ''')
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        # 库名称
        name_layout = QVBoxLayout()
        name_label = QLabel('库名称 *')
        name_label.setStyleSheet(f'color: {COLORS["text_primary"]}; font-weight: 600; font-size: 13px;')
        name_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('输入库的名称，如：我的文档库')
        self.name_input.setMinimumHeight(36)
        self.name_input.setStyleSheet(LINE_EDIT_STYLE)
        name_layout.addWidget(self.name_input)
        form_layout.addLayout(name_layout)
        
        # 存储位置
        path_layout = QVBoxLayout()
        path_label = QLabel('存储位置 *')
        path_label.setStyleSheet(f'color: {COLORS["text_primary"]}; font-weight: 600; font-size: 13px;')
        path_layout.addWidget(path_label)
        
        path_input_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText('选择存储位置')
        self.path_input.setReadOnly(True)
        self.path_input.setMinimumHeight(36)
        self.path_input.setStyleSheet(LINE_EDIT_STYLE)
        path_input_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton('浏览...')
        browse_btn.setMinimumHeight(36)
        browse_btn.setMinimumWidth(80)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        browse_btn.clicked.connect(self.browse_location)
        path_input_layout.addWidget(browse_btn)
        path_layout.addLayout(path_input_layout)
        form_layout.addLayout(path_layout)
        
        # 描述
        desc_layout = QVBoxLayout()
        desc_label = QLabel('描述（可选）')
        desc_label.setStyleSheet(f'color: {COLORS["text_primary"]}; font-weight: 600; font-size: 13px;')
        desc_layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText('输入库的描述信息...')
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet(TEXT_EDIT_STYLE)
        desc_layout.addWidget(self.desc_input)
        form_layout.addLayout(desc_layout)
        
        layout.addWidget(form_frame)
        
        layout.addStretch()
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton('取消')
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton('✓ 创建')
        create_btn.setMinimumWidth(100)
        create_btn.setMinimumHeight(36)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        create_btn.clicked.connect(self.create_library)
        btn_layout.addWidget(create_btn)
        
        layout.addLayout(btn_layout)
    
    def browse_location(self):
        """浏览选择位置"""
        # 获取上次打开的位置，如果没有则使用用户目录
        start_path = get_last_opened_path() or str(Path.home())
        
        path = QFileDialog.getExistingDirectory(
            self,
            '选择存储位置',
            start_path,
            QFileDialog.Option.ShowDirsOnly
        )
        if path:
            self.selected_path = path
            self.path_input.setText(path)
            save_last_opened_path(path)
    
    def create_library(self):
        """创建库"""
        name = self.name_input.text().strip()
        base_path = self.selected_path
        description = self.desc_input.toPlainText().strip()
        
        # 验证
        if not name:
            QMessageBox.warning(self, '验证失败', '请输入库名称')
            return
        
        if not base_path:
            QMessageBox.warning(self, '验证失败', '请选择存储位置')
            return
        
        # 在选定的路径下创建以库名命名的子文件夹
        import re
        # 将库名转换为安全的文件夹名（移除非法字符）
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', name)
        if not safe_name:
            safe_name = 'library'
        
        # 构建完整的库路径
        path = os.path.join(base_path, safe_name)
        
        # 检查路径是否已存在
        if os.path.exists(path):
            QMessageBox.warning(self, '验证失败', f'文件夹已存在: {safe_name}\n请更换库名称或选择其他位置')
            return
        
        try:
            manager = LibraryManager()
            library = manager.create_library(name, path, description)
            self.library_created.emit(library)
            self.accept()
        except FileExistsError as e:
            QMessageBox.warning(self, '创建失败', str(e))
        except PermissionError as e:
            QMessageBox.warning(self, '创建失败', str(e))
        except Exception as e:
            QMessageBox.critical(self, '错误', f'创建库时发生错误：{str(e)}')


class WelcomeDialog(QDialog):
    """欢迎对话框 - VS2019 Dark风格"""
    
    library_selected = pyqtSignal(LibraryInfo)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('欢迎使用文档管家')
        self.setMinimumSize(800, 560)
        self.setModal(True)
        self.library_manager = LibraryManager()
        self.setup_ui()
        self.load_recent_libraries()
    
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧 - 欢迎信息
        left_panel = QWidget()
        left_panel.setStyleSheet(f'''
            QWidget {{
                background-color: {COLORS['bg_secondary']};
            }}
        ''')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(48, 56, 48, 48)
        left_layout.setSpacing(20)
        
        # Logo/标题
        title = QLabel('📁 文档管家')
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f'color: {COLORS["text_highlight"]};')
        left_layout.addWidget(title)
        
        # 副标题
        subtitle = QLabel('智能文档分类管理系统')
        subtitle_font = QFont()
        subtitle_font.setPointSize(13)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet(f'color: {COLORS["text_secondary"]};')
        left_layout.addWidget(subtitle)
        
        left_layout.addSpacing(40)
        
        # 功能介绍
        features_title = QLabel('功能特性')
        features_title.setStyleSheet(f'color: {COLORS["text_primary"]}; font-size: 14px; font-weight: 600;')
        left_layout.addWidget(features_title)
        
        features = QLabel(
            '⚡ 智能文件夹自动分类\n'
            '🏷️ 层级标签管理\n'
            '👁️ 实时监控自动导入\n'
            '🔍 全文搜索支持'
        )
        features.setStyleSheet(f'color: {COLORS["text_secondary"]}; font-size: 13px; line-height: 2;')
        left_layout.addWidget(features)
        
        left_layout.addStretch()
        
        # 版本信息
        version = QLabel('版本 1.0.0')
        version.setStyleSheet(f'color: {COLORS["text_disabled"]}; font-size: 11px;')
        left_layout.addWidget(version)
        
        main_layout.addWidget(left_panel, 1)
        
        # 右侧 - 操作区域
        right_panel = QWidget()
        right_panel.setStyleSheet(f'''
            QWidget {{
                background-color: {COLORS['bg_primary']};
            }}
        ''')
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(48, 48, 48, 48)
        right_layout.setSpacing(24)
        
        # 欢迎标题
        welcome_title = QLabel('开始使用')
        welcome_font = QFont()
        welcome_font.setPointSize(24)
        welcome_font.setBold(True)
        welcome_title.setFont(welcome_font)
        welcome_title.setStyleSheet(f'color: {COLORS["text_highlight"]};')
        right_layout.addWidget(welcome_title)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        create_btn = QPushButton('+ 创建新库')
        create_btn.setMinimumHeight(44)
        create_btn.setMinimumWidth(140)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        create_btn.clicked.connect(self.show_create_dialog)
        btn_layout.addWidget(create_btn)
        
        open_btn = QPushButton('打开已有库')
        open_btn.setMinimumHeight(44)
        open_btn.setMinimumWidth(140)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        open_btn.clicked.connect(self.open_existing_library)
        btn_layout.addWidget(open_btn)
        
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)
        
        # 最近使用的库
        recent_label = QLabel('最近使用的库')
        recent_font = QFont()
        recent_font.setPointSize(14)
        recent_font.setBold(True)
        recent_label.setFont(recent_font)
        recent_label.setStyleSheet(f'color: {COLORS["text_primary"]};')
        right_layout.addWidget(recent_label)
        
        # 库列表
        self.library_list = QListWidget()
        self.library_list.setStyleSheet(LIST_WIDGET_STYLE)
        self.library_list.itemClicked.connect(self.on_library_selected)
        self.library_list.itemDoubleClicked.connect(self.on_library_double_clicked)
        right_layout.addWidget(self.library_list)
        
        # 空状态提示
        self.empty_label = QLabel('暂无最近使用的库')
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f'color: {COLORS["text_disabled"]}; padding: 40px; font-size: 13px;')
        right_layout.addWidget(self.empty_label)
        
        right_layout.addStretch()
        
        main_layout.addWidget(right_panel, 2)
    
    def load_recent_libraries(self):
        """加载最近使用的库"""
        libraries = self.library_manager.get_recent_libraries()
        
        self.library_list.clear()
        
        if libraries:
            self.empty_label.hide()
            for library in libraries:
                item = QListWidgetItem()
                item_widget = LibraryListItem(library)
                item.setSizeHint(item_widget.sizeHint())
                item.setData(Qt.ItemDataRole.UserRole, library)
                self.library_list.addItem(item)
                self.library_list.setItemWidget(item, item_widget)
        else:
            self.empty_label.show()
    
    def on_library_selected(self, item: QListWidgetItem):
        """库被选中"""
        library = item.data(Qt.ItemDataRole.UserRole)
    
    def on_library_double_clicked(self, item: QListWidgetItem):
        """库被双击打开"""
        library = item.data(Qt.ItemDataRole.UserRole)
        self.library_selected.emit(library)
        self.accept()
    
    def show_create_dialog(self):
        """显示创建库对话框"""
        dialog = CreateLibraryDialog(self)
        dialog.library_created.connect(self.on_library_created)
        dialog.exec()
    
    def on_library_created(self, library: LibraryInfo):
        """库创建完成"""
        self.library_selected.emit(library)
        self.accept()
    
    def open_existing_library(self):
        """打开已有库"""
        # 获取上次打开的位置
        start_path = get_last_opened_path() or str(Path.home())
        
        path = QFileDialog.getExistingDirectory(
            self,
            '选择文档库文件夹',
            start_path,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not path:
            return
        
        # 检查是否是有效的库
        if not self.library_manager.is_valid_library(path):
            # 检查是否存在 library.db 文件
            db_path = os.path.join(path, 'library.db')
            if not os.path.exists(db_path):
                QMessageBox.warning(
                    self,
                    '无效的库',
                    f'选择的文件夹不是有效的文档库。\n\n'
                    f'未找到 library.db 文件。\n'
                    f'路径: {path}'
                )
            else:
                QMessageBox.warning(
                    self,
                    '无效的库',
                    f'library.db 文件存在但格式不正确。\n\n'
                    f'路径: {path}'
                )
            return
        
        library = self.library_manager.open_library(path)
        if library:
            save_last_opened_path(path)
            self.library_selected.emit(library)
            self.accept()
        else:
            QMessageBox.critical(
                self, 
                '错误', 
                f'无法打开文档库\n\n'
                f'路径: {path}\n'
                f'请检查库文件是否损坏。'
            )
