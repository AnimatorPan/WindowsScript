"""
主窗口 - Visual Studio 2019 Dark 主题
"""

import os
import sys
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSplitter, QStackedWidget,
    QStatusBar, QMenuBar, QMenu, QFileDialog, QMessageBox,
    QFrame, QTreeWidget, QTreeWidgetItem, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QFont

# 修复导入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.library import LibraryInfo, LibraryManager
from gui.styles.app_styles import (
    get_app_stylesheet, COLORS, 
    PRIMARY_BUTTON_STYLE, DEFAULT_BUTTON_STYLE, SIDEBAR_BUTTON_STYLE
)
from gui.components.dialogs.welcome_dialog import WelcomeWindow
from gui.components.dialogs.import_dialog import ImportDialog


class Sidebar(QWidget):
    """侧边栏组件 - VS2019 Dark风格"""
    
    item_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sidebar')
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 设置侧边栏背景
        self.setStyleSheet(f'''
            QWidget#sidebar {{
                background-color: {COLORS['bg_secondary']};
                border-right: 1px solid {COLORS['border']};
            }}
        ''')
        
        # 标题区域
        header = QWidget()
        header.setStyleSheet(f'background-color: {COLORS["bg_secondary"]};')
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 20, 16, 16)
        header_layout.setSpacing(6)
        
        # 应用标题
        title = QLabel('📁 文档管家')
        title.setStyleSheet(f'''
            color: {COLORS['text_highlight']};
            font-size: 16px;
            font-weight: 600;
        ''')
        header_layout.addWidget(title)
        
        # 库名称
        self.library_label = QLabel('未选择库')
        self.library_label.setStyleSheet(f'''
            color: {COLORS['text_secondary']};
            font-size: 12px;
            padding-top: 4px;
        ''')
        header_layout.addWidget(self.library_label)
        
        layout.addWidget(header)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f'background-color: {COLORS["border"]};')
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # 导航区域
        nav_container = QWidget()
        nav_container.setStyleSheet(f'background-color: {COLORS["bg_secondary"]};')
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(12, 16, 12, 12)
        nav_layout.setSpacing(4)
        
        # 导航项
        nav_items = [
            ('all', '📄', '全部文档'),
            ('categories', '📂', '分类'),
            ('tags', '🏷️', '标签'),
            ('smart', '⚡', '智能文件夹'),
            ('watched', '👁️', '监控文件夹'),
        ]
        
        self.nav_buttons = {}
        for item_id, icon, item_text in nav_items:
            btn = QPushButton(f'{icon}  {item_text}')
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(40)
            # 直接应用侧边栏按钮样式
            btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
            btn.clicked.connect(lambda checked, id=item_id: self.on_nav_clicked(id))
            nav_layout.addWidget(btn)
            self.nav_buttons[item_id] = btn
        
        nav_layout.addStretch()
        
        # 底部设置按钮
        settings_separator = QFrame()
        settings_separator.setFrameShape(QFrame.Shape.HLine)
        settings_separator.setStyleSheet(f'background-color: {COLORS["border"]};')
        settings_separator.setFixedHeight(1)
        nav_layout.addWidget(settings_separator)
        
        settings_btn = QPushButton('⚙️  设置')
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setMinimumHeight(40)
        settings_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        nav_layout.addWidget(settings_btn)
        
        layout.addWidget(nav_container)
    
    def on_nav_clicked(self, item_id: str):
        """导航项被点击"""
        for id, btn in self.nav_buttons.items():
            btn.setChecked(id == item_id)
        self.item_selected.emit(item_id)
    
    def set_library_name(self, name: str):
        """设置当前库名称"""
        self.library_label.setText(name)


class MainContent(QWidget):
    """主内容区 - VS2019 Dark风格"""
    
    import_requested = pyqtSignal()  # 导入请求信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 先设置背景色
        self.setStyleSheet(f'''
            MainContent {{
                background-color: {COLORS['bg_primary']};
            }}
        ''')
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        # 标题
        self.title_label = QLabel('全部文档')
        self.title_label.setStyleSheet(f'''
            color: {COLORS['text_highlight']};
            font-size: 24px;
            font-weight: 600;
        ''')
        toolbar.addWidget(self.title_label)
        
        toolbar.addStretch()
        
        # 搜索按钮
        search_btn = QPushButton('🔍 搜索')
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setMinimumHeight(36)
        search_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        toolbar.addWidget(search_btn)
        
        # 视图切换按钮
        view_btn = QPushButton('☰ 列表')
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.setMinimumHeight(36)
        view_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        toolbar.addWidget(view_btn)
        
        # 导入按钮
        import_btn = QPushButton('+ 导入文档')
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.setMinimumHeight(36)
        import_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        import_btn.clicked.connect(self.on_import_clicked)
        toolbar.addWidget(import_btn)
        
        layout.addLayout(toolbar)
        
        # 内容区域
        content_frame = QFrame()
        content_frame.setObjectName('contentFrame')
        content_frame.setStyleSheet(f'''
            QFrame#contentFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        ''')
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 内容堆叠器
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f'background-color: {COLORS["bg_secondary"]}; border: none;')
        
        # 全部文档页面
        self.all_docs_page = self.create_all_docs_page()
        self.stack.addWidget(self.all_docs_page)
        
        # 其他页面占位
        self.categories_page = self.create_placeholder_page('分类管理')
        self.stack.addWidget(self.categories_page)
        
        self.tags_page = self.create_placeholder_page('标签管理')
        self.stack.addWidget(self.tags_page)
        
        self.smart_page = self.create_placeholder_page('智能文件夹')
        self.stack.addWidget(self.smart_page)
        
        self.watched_page = self.create_placeholder_page('监控文件夹')
        self.stack.addWidget(self.watched_page)
        
        content_layout.addWidget(self.stack)
        layout.addWidget(content_frame)
    
    def on_import_clicked(self):
        """导入按钮被点击"""
        self.import_requested.emit()
    
    def create_all_docs_page(self):
        """创建全部文档页面"""
        page = QWidget()
        page.setStyleSheet(f'background-color: {COLORS["bg_secondary"]};')
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 空状态
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(20)
        
        # 图标
        icon_label = QLabel('📁')
        icon_label.setStyleSheet('font-size: 72px;')
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_label)
        
        # 主文字
        empty_label = QLabel('暂无文档')
        empty_label.setStyleSheet(f'''
            color: {COLORS['text_secondary']};
            font-size: 20px;
            font-weight: 500;
        ''')
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_label)
        
        # 提示文字
        empty_hint = QLabel('点击"导入文档"按钮添加您的第一个文档\n或拖拽文件到此处')
        empty_hint.setStyleSheet(f'''
            color: {COLORS['text_disabled']};
            font-size: 14px;
            line-height: 1.6;
        ''')
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_hint)
        
        # 快捷按钮
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        quick_import = QPushButton('+ 导入文档')
        quick_import.setCursor(Qt.CursorShape.PointingHandCursor)
        quick_import.setMinimumHeight(40)
        quick_import.setMinimumWidth(120)
        quick_import.setStyleSheet(PRIMARY_BUTTON_STYLE)
        btn_layout.addWidget(quick_import)
        
        empty_layout.addLayout(btn_layout)
        
        layout.addWidget(self.empty_widget)
        
        # 文档列表（初始隐藏）
        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(5)
        self.doc_table.setHorizontalHeaderLabels(['文件名', '类型', '大小', '修改时间', '标签'])
        self.doc_table.horizontalHeader().setStretchLastSection(True)
        self.doc_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.doc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.doc_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.doc_table.setAlternatingRowColors(True)
        self.doc_table.verticalHeader().setVisible(False)
        self.doc_table.setStyleSheet(f'''
            QTableWidget {{
                background-color: {COLORS['bg_secondary']};
                border: none;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {COLORS['border']};
                color: {COLORS['text_primary']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['bg_selected']};
                color: {COLORS['text_highlight']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                padding: 12px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                border-right: 1px solid {COLORS['border']};
                font-weight: 600;
            }}
        ''')
        self.doc_table.hide()
        layout.addWidget(self.doc_table)
        
        return page
    
    def load_documents(self, library_path: str = None):
        """加载文档列表"""
        if not library_path:
            return
        
        db_path = os.path.join(library_path, 'library.db')
        if not os.path.exists(db_path):
            return
        
        try:
            from core.database import Database
            db = Database(db_path).connect()
            
            # 检查表结构
            cursor = db._connection.execute("PRAGMA table_info(documents)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'name' in columns:
                # 新表结构
                rows = db.fetchall(
                    'SELECT name, file_type, file_size, modified_at, tags FROM documents ORDER BY imported_at DESC'
                )
            elif 'filename' in columns:
                # 旧表结构
                rows = db.fetchall(
                    'SELECT filename as name, file_type, size as file_size, modified_at, "" as tags FROM documents ORDER BY imported_at DESC'
                )
            else:
                rows = []
            
            db.close()
            
            if rows:
                # 显示表格，隐藏空状态
                self.empty_widget.hide()
                self.doc_table.show()
                
                # 填充数据
                self.doc_table.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    # 文件名
                    name_item = QTableWidgetItem(row['name'])
                    self.doc_table.setItem(i, 0, name_item)
                    
                    # 类型
                    file_type = row['file_type'] if 'file_type' in row.keys() else ''
                    type_item = QTableWidgetItem(file_type)
                    self.doc_table.setItem(i, 1, type_item)
                    
                    # 大小
                    file_size = row['file_size'] if 'file_size' in row.keys() else 0
                    size_str = self.format_size(file_size)
                    size_item = QTableWidgetItem(size_str)
                    self.doc_table.setItem(i, 2, size_item)
                    
                    # 修改时间
                    modified_at = row['modified_at'] if 'modified_at' in row.keys() else ''
                    modified_item = QTableWidgetItem(str(modified_at)[:19] if modified_at else '')
                    self.doc_table.setItem(i, 3, modified_item)
                    
                    # 标签
                    tags = row['tags'] if 'tags' in row.keys() else ''
                    tags_item = QTableWidgetItem(tags)
                    self.doc_table.setItem(i, 4, tags_item)
            else:
                # 显示空状态
                self.empty_widget.show()
                self.doc_table.hide()
                
        except Exception as e:
            print(f"[DEBUG] 加载文档失败: {e}")
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f'{size_bytes} B'
        elif size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.1f} KB'
        elif size_bytes < 1024 * 1024 * 1024:
            return f'{size_bytes / (1024 * 1024):.1f} MB'
        else:
            return f'{size_bytes / (1024 * 1024 * 1024):.1f} GB'
    
    def create_placeholder_page(self, title_text):
        """创建占位页面"""
        page = QWidget()
        page.setStyleSheet(f'background-color: {COLORS["bg_secondary"]};')
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        icon_label = QLabel('🚧')
        icon_label.setStyleSheet('font-size: 56px;')
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        title = QLabel(title_text)
        title.setStyleSheet(f'''
            color: {COLORS['text_secondary']};
            font-size: 18px;
            font-weight: 500;
        ''')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        hint = QLabel('功能开发中...')
        hint.setStyleSheet(f'color: {COLORS["text_disabled"]}; font-size: 14px;')
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        
        return page
    
    def set_page(self, index: int, title: str):
        """切换页面"""
        self.title_label.setText(title)
        self.stack.setCurrentIndex(index)


class MainWindow(QMainWindow):
    """主窗口 - VS2019 Dark主题"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('文档管家')
        self.setMinimumSize(1280, 800)
        
        # 设置主窗口背景色
        self.setStyleSheet(f'''
            QMainWindow {{
                background-color: {COLORS['bg_primary']};
            }}
        ''')
        
        # 应用全局样式（在设置中央部件后）
        # 先不应用全局样式，避免覆盖
        
        # 当前库
        self.current_library: Optional[LibraryInfo] = None
        self.library_manager = LibraryManager()
        
        self.setup_ui()
        self.setup_menu()
        
        # 启动时显示欢迎对话框
        self.show_welcome_dialog()
    
    def setup_ui(self):
        """设置UI"""
        # 中央部件 - 设置深色背景
        central_widget = QWidget()
        central_widget.setStyleSheet(f'background-color: {COLORS["bg_primary"]};')
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 分割器 - 设置深色背景
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f'''
            QSplitter {{
                background-color: {COLORS['bg_primary']};
            }}
            QSplitter::handle {{
                background-color: {COLORS['border']};
            }}
        ''')
        
        # 侧边栏
        self.sidebar = Sidebar()
        self.sidebar.item_selected.connect(self.on_sidebar_item_selected)
        splitter.addWidget(self.sidebar)
        
        # 主内容区
        self.main_content = MainContent()
        self.main_content.import_requested.connect(self.import_documents)
        splitter.addWidget(self.main_content)
        
        # 设置分割比例
        splitter.setSizes([240, 1040])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')
        self.status_bar.setStyleSheet(f'''
            QStatusBar {{
                background-color: {COLORS['accent']};
                color: {COLORS['text_highlight']};
                border-top: 1px solid {COLORS['border']};
            }}
        ''')
    
    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet(f'''
            QMenuBar {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border-bottom: 1px solid {COLORS['border']};
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 6px 12px;
            }}
            QMenuBar::item:selected {{
                background-color: {COLORS['bg_selected']};
                color: {COLORS['text_highlight']};
            }}
        ''')
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        file_menu.setStyleSheet(f'''
            QMenu {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['bg_selected']};
                color: {COLORS['text_highlight']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {COLORS['border']};
                margin: 4px 8px;
            }}
        ''')
        
        new_lib_action = QAction('新建库', self)
        new_lib_action.setShortcut(QKeySequence.StandardKey.New)
        new_lib_action.triggered.connect(self.show_welcome_dialog)
        file_menu.addAction(new_lib_action)
        
        open_lib_action = QAction('打开库', self)
        open_lib_action.setShortcut(QKeySequence.StandardKey.Open)
        open_lib_action.triggered.connect(self.open_library)
        file_menu.addAction(open_lib_action)
        
        file_menu.addSeparator()
        
        import_action = QAction('导入文档', self)
        import_action.triggered.connect(self.import_documents)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_welcome_dialog(self):
        """显示欢迎对话框"""
        self.welcome_window = WelcomeWindow(self)
        self.welcome_window.library_selected.connect(self.on_library_selected)
        self.welcome_window.show()
    
    def on_library_selected(self, library: LibraryInfo):
        """库被选中"""
        self.current_library = library
        self.sidebar.set_library_name(library.name)
        self.setWindowTitle(f'文档管家 - {library.name}')
        self.status_bar.showMessage(f'已打开库: {library.path}')
        # 加载文档列表
        self.main_content.load_documents(library.path)
    
    def on_sidebar_item_selected(self, item_id: str):
        """侧边栏项被选中"""
        page_map = {
            'all': (0, '全部文档'),
            'categories': (1, '分类'),
            'tags': (2, '标签'),
            'smart': (3, '智能文件夹'),
            'watched': (4, '监控文件夹'),
        }
        
        if item_id in page_map:
            index, title = page_map[item_id]
            self.main_content.set_page(index, title)
    
    def open_library(self):
        """打开已有库"""
        path = QFileDialog.getExistingDirectory(
            self,
            '选择文档库文件夹',
            os.path.expanduser('~')
        )
        
        if not path:
            return
        
        if not self.library_manager.is_valid_library(path):
            QMessageBox.warning(
                self,
                '无效的库',
                '选择的文件夹不是有效的文档库。'
            )
            return
        
        library = self.library_manager.open_library(path)
        if library:
            self.on_library_selected(library)
        else:
            QMessageBox.critical(self, '错误', '无法打开文档库')
    
    def import_documents(self):
        """导入文档"""
        if not self.current_library:
            QMessageBox.warning(self, '提示', '请先打开或创建一个文档库')
            return
        
        # 显示导入对话框
        dialog = ImportDialog(self.current_library.path, self)
        dialog.import_completed.connect(self.on_import_completed)
        dialog.exec()
    
    def on_import_completed(self, count):
        """导入完成"""
        self.status_bar.showMessage(f'成功导入 {count} 个文档')
        # 刷新文档列表
        if self.current_library:
            self.main_content.load_documents(self.current_library.path)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            '关于文档管家',
            '<h2>文档管家 1.0.0</h2>'
            '<p>智能文档分类管理系统</p>'
            '<p>功能特性：</p>'
            '<ul>'
            '<li>智能文件夹自动分类</li>'
            '<li>层级标签管理</li>'
            '<li>实时监控自动导入</li>'
            '<li>全文搜索支持</li>'
            '</ul>'
        )
