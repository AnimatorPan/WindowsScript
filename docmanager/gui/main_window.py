"""
主窗口（完整更新版）
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from pathlib import Path
import logging

from core.database import Database
from core.library import LibraryManager
from gui.components.toolbar import Toolbar
from gui.components.sidebar import Sidebar
from gui.components.document_area import DocumentArea
from gui.components.detail_panel import DetailPanel
from gui.components.statusbar import StatusBar
from gui.dialogs.import_dialog import ImportDialog
from gui.welcome_dialog import WelcomeDialog
from utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """主窗口（完整版）"""
    
    library_changed = pyqtSignal(int)
    document_selected = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        
        self.db = None
        self.library_id = None
        self.current_library = None
        
        self.init_ui()
        self.show_welcome()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("DocManager - 文档管家")
        self.setGeometry(100, 100, 1400, 900)
        
        self.create_menu_bar()
        
        self.toolbar = Toolbar(self)
        self.addToolBar(self.toolbar)
        
        self.create_central_widget()
        
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)
        
        self.connect_signals()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        new_action = QAction("新建库(&N)", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.show_welcome)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开库(&O)", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.show_welcome)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("导入文档(&I)", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.show_import_dialog)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        select_all_action = QAction("全选(&A)", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        edit_menu.addAction(select_all_action)
        
        # 查看菜单
        view_menu = menubar.addMenu("查看(&V)")
        
        list_view_action = QAction("列表视图(&L)", self)
        list_view_action.triggered.connect(lambda: self.document_area.switch_view('list'))
        view_menu.addAction(list_view_action)
        
        grid_view_action = QAction("网格视图(&G)", self)
        grid_view_action.triggered.connect(lambda: self.document_area.switch_view('grid'))
        view_menu.addAction(grid_view_action)
        
        view_menu.addSeparator()
        
        stats_action = QAction("统计报表(&S)", self)
        stats_action.triggered.connect(self.show_statistics)
        view_menu.addAction(stats_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        category_action = QAction("管理分类(&C)", self)
        category_action.triggered.connect(self.show_category_manager)
        tools_menu.addAction(category_action)
        
        tag_action = QAction("管理标签(&G)", self)
        tag_action.triggered.connect(self.show_tag_manager)
        tools_menu.addAction(tag_action)
        
        tools_menu.addSeparator()
        
        unorganized_action = QAction("待整理中心(&U)", self)
        unorganized_action.setShortcut("Ctrl+U")
        unorganized_action.triggered.connect(self.show_unorganized_center)
        tools_menu.addAction(unorganized_action)
        
        advanced_search_action = QAction("高级搜索(&F)", self)
        advanced_search_action.setShortcut("Ctrl+Shift+F")
        advanced_search_action.triggered.connect(self.show_advanced_search)
        tools_menu.addAction(advanced_search_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("设置(&S)", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_central_widget(self):
        """创建中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧边栏
        self.sidebar = Sidebar(self)
        self.sidebar.setMinimumWidth(180)
        self.sidebar.setMaximumWidth(300)
        splitter.addWidget(self.sidebar)
        
        # 中间内容区
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 文档内容区（含列表/网格切换）
        self.document_area = DocumentArea(self)
        content_splitter.addWidget(self.document_area)
        
        # 详情面板
        self.detail_panel = DetailPanel(self)
        self.detail_panel.setMinimumWidth(240)
        self.detail_panel.setMaximumWidth(400)
        content_splitter.addWidget(self.detail_panel)
        
        content_splitter.setStretchFactor(0, 7)
        content_splitter.setStretchFactor(1, 3)
        
        splitter.addWidget(content_splitter)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 8)
        
        main_layout.addWidget(splitter)
    
    def connect_signals(self):
        """连接信号（完整版）"""
        # 工具栏
        self.toolbar.import_clicked.connect(self.show_import_dialog)
        self.toolbar.search_triggered.connect(self.on_search)
        self.toolbar.advanced_search_clicked.connect(self.show_advanced_search)
        self.toolbar.view_list_clicked.connect(
            lambda: self.document_area.switch_view('list'))
        self.toolbar.view_grid_clicked.connect(
            lambda: self.document_area.switch_view('grid'))
        self.toolbar.unorganized_clicked.connect(self.show_unorganized_center)
        self.toolbar.statistics_clicked.connect(self.show_statistics)

        # 侧边栏
        self.sidebar.all_documents_clicked.connect(self.on_all_documents)
        self.sidebar.category_selected.connect(self.on_category_selected)
        self.sidebar.tag_selected.connect(self.on_tag_selected)
        self.sidebar.smart_folder_selected.connect(self.on_smart_folder_selected)
        self.sidebar.uncategorized_clicked.connect(self.on_uncategorized)
        self.sidebar.untagged_clicked.connect(self.on_untagged)
        self.sidebar.duplicates_clicked.connect(self.on_duplicates)
        self.sidebar.sidebar_refreshed.connect(self.on_sidebar_refreshed)

        # 文档内容区
        self.document_area.document_selected.connect(self.on_document_selected)
        self.document_area.selection_changed.connect(self.on_selection_changed)
        self.document_area.documents_updated.connect(self.on_documents_updated)

        # 详情面板
        self.detail_panel.document_updated.connect(self.on_document_updated)

        # 库切换
        self.library_changed.connect(self.on_library_changed)
    def show_welcome(self):
        """显示欢迎对话框"""
        dialog = WelcomeDialog(self)
        if dialog.exec():
            library_info = dialog.get_selected_library()
            if library_info:
                self.open_library(library_info['id'], library_info['db_path'])
    
    def open_library(self, library_id: int, db_path: str):
        """打开库"""
        try:
            if not Path(db_path).exists():
                raise FileNotFoundError(f"数据库文件不存在: {db_path}")

            if self.db:
                self.db.close()

            self.db = Database(db_path)
            self.db.connect()
            self.library_id = library_id

            lib_manager = LibraryManager(self.db)
            self.current_library = lib_manager.get(library_id)

            if not self.current_library:
                raise ValueError(f"找不到库记录: ID={library_id}")

            self.setWindowTitle(f"DocManager - {self.current_library['name']}")
            self.library_changed.emit(library_id)
            self.status_bar.show_message(f"已打开库: {self.current_library['name']}")

            # 记录到最近打开
            config = ConfigManager()
            config.add_recent_library(
                library_id, self.current_library['name'], db_path)

            logger.info(f"库打开成功: {self.current_library['name']}")

        except Exception as e:
            logger.error(f"打开库失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"打开库失败:\n\n{str(e)}")
    
    def on_library_changed(self, library_id: int):
        """库切换后加载数据"""
        if not self.db or not library_id:
            return
        
        try:
            self.sidebar.load_library(library_id)
            self.on_all_documents()
        
        except Exception as e:
            logger.error(f"加载库数据失败: {e}", exc_info=True)
    
    def on_all_documents(self):
        """显示全部文档"""
        if not self.db or not self.library_id:
            return
        
        try:
            from core.document import DocumentManager
            
            doc_manager = DocumentManager(self.db, self.library_id)
            docs = doc_manager.list_all(limit=1000)
            
            self.document_area.load_documents(docs)
            self.status_bar.show_message(f"全部文档: {len(docs)} 个")
        
        except Exception as e:
            logger.error(f"加载文档失败: {e}", exc_info=True)
    
    def show_import_dialog(self):
        """显示导入对话框"""
        if not self.db or not self.library_id:
            QMessageBox.warning(self, "提示", "请先打开一个库")
            return
        
        dialog = ImportDialog(
            self.db,
            self.library_id,
            self.current_library['storage_path'],
            self
        )
        dialog.import_completed.connect(self.on_import_completed)
        dialog.exec()
    
    def show_statistics(self):
        """显示统计报表"""
        if not self.db or not self.library_id:
            QMessageBox.warning(self, "提示", "请先打开一个库")
            return
        
        from gui.statistics_window import StatisticsWindow
        
        window = StatisticsWindow(self.db, self.library_id, self)
        window.show()
    
    def show_category_manager(self):
        """显示分类管理"""
        if not self.db or not self.library_id:
            QMessageBox.warning(self, "提示", "请先打开一个库")
            return
        
        from gui.dialogs.category_dialog import CategoryDialog
        
        dialog = CategoryDialog(self.db, self.library_id, self)
        dialog.exec()
        
        # 刷新侧边栏
        self.sidebar.load_categories()
    
    def show_tag_manager(self):
        """显示标签管理"""
        if not self.db or not self.library_id:
            QMessageBox.warning(self, "提示", "请先打开一个库")
            return
        
        from gui.dialogs.tag_dialog import TagDialog
        
        dialog = TagDialog(self.db, self.library_id, self)
        dialog.exec()
        
        # 刷新侧边栏
        self.sidebar.load_tags()
    
    def show_unorganized_center(self):
        """显示待整理中心"""
        if not self.db or not self.library_id:
            QMessageBox.warning(self, "提示", "请先打开一个库")
            return
        
        from gui.unorganized_center import UnorganizedCenter
        
        window = UnorganizedCenter(self.db, self.library_id, self)
        window.show()
    
    def show_advanced_search(self):
        """显示高级搜索"""
        if not self.db or not self.library_id:
            QMessageBox.warning(self, "提示", "请先打开一个库")
            return
        
        from gui.dialogs.advanced_search_dialog import AdvancedSearchDialog
        
        dialog = AdvancedSearchDialog(self.db, self.library_id, self)
        dialog.search_triggered.connect(self.on_advanced_search)
        dialog.show()
    
    def show_settings(self):
        """显示设置"""
        from gui.dialogs.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def on_search(self, keyword: str):
        """基础搜索"""
        if not self.db or not self.library_id:
            return
        
        from core.search import SearchEngine
        
        search_engine = SearchEngine(self.db, self.library_id)
        results = search_engine.search_by_filename(keyword)
        
        self.document_area.load_documents(results)
        self.status_bar.show_message(f"搜索 '{keyword}': 找到 {len(results)} 个文档")
    
    def on_advanced_search(self, filters: dict):
        """高级搜索"""
        if not self.db or not self.library_id:
            return
        
        from core.search import SearchEngine
        
        search_engine = SearchEngine(self.db, self.library_id)
        results = search_engine.complex_search(filters)
        
        self.document_area.load_documents(results)
        self.status_bar.show_message(f"高级搜索: 找到 {len(results)} 个文档")
    
    def on_category_selected(self, category_id: int):
        """分类选中"""
        if not self.db or not self.library_id:
            return
        
        from core.document import DocumentManager
        
        doc_manager = DocumentManager(self.db, self.library_id)
        docs = doc_manager.list_by_category(category_id)
        
        self.document_area.load_documents(docs)
        self.status_bar.show_message(f"分类文档: {len(docs)} 个")
    
    def on_tag_selected(self, tag_id: int):
        """标签选中"""
        if not self.db or not self.library_id:
            return
        
        from core.document import DocumentManager
        
        doc_manager = DocumentManager(self.db, self.library_id)
        docs = doc_manager.list_by_tag(tag_id)
        
        self.document_area.load_documents(docs)
        self.status_bar.show_message(f"标签文档: {len(docs)} 个")
    
    def on_smart_folder_selected(self, folder_id: int):
        """智能文件夹选中"""
        if not self.db or not self.library_id:
            return
        
        from core.smart_folder import SmartFolderManager
        
        sf_manager = SmartFolderManager(self.db, self.library_id)
        docs = sf_manager.get_matched_documents(folder_id)
        
        self.document_area.load_documents(docs)
        self.status_bar.show_message(f"智能文件夹: {len(docs)} 个文档")
    
    def on_document_selected(self, document_id: int):
        """文档选中"""
        self.document_selected.emit(document_id)
        self.detail_panel.load_document(document_id)
    
    def on_selection_changed(self, count: int):
        """选择数量变化"""
        if count == 0:
            self.status_bar.show_message("就绪")
        else:
            self.status_bar.show_message(f"已选择 {count} 个文档")
    
    def on_documents_updated(self):
        """文档更新后刷新"""
        self.on_all_documents()
    
    def on_document_updated(self):
        """文档信息更新"""
        pass
    
    def on_import_completed(self, result):
        """导入完成"""
        self.status_bar.show_message(
            f"导入完成: 成功 {result.success}, 重复 {result.duplicate}, 失败 {result.failed}"
        )
        self.on_all_documents()
        self.sidebar.load_library(self.library_id)
    
    def show_about(self):
        """关于"""
        QMessageBox.about(
            self,
            "关于 DocManager",
            "<h3>DocManager - 文档管家</h3>"
            "<p>版本: 1.0.0</p>"
            "<p>面向小团队的文档分类管理系统</p>"
            "<br>"
            "<p><b>功能特性:</b></p>"
            "<ul>"
            "<li>统一管理团队文档</li>"
            "<li>分类与标签组织</li>"
            "<li>智能文件夹</li>"
            "<li>去重管理</li>"
            "<li>批量操作</li>"
            "</ul>"
        )
    
    def on_uncategorized(self):
        """显示未分类文档"""
        if not self.db or not self.library_id:
            return

        from core.document import DocumentManager

        doc_manager = DocumentManager(self.db, self.library_id)
        docs = doc_manager.list_uncategorized()

        self.document_area.load_documents(docs)
        self.status_bar.show_message(f"未分类文档: {len(docs)} 个")
    def on_untagged(self):
        """显示未打标签文档"""
        if not self.db or not self.library_id:
            return

        from core.document import DocumentManager

        doc_manager = DocumentManager(self.db, self.library_id)
        docs = doc_manager.list_untagged()

        self.document_area.load_documents(docs)
        self.status_bar.show_message(f"未打标签文档: {len(docs)} 个")


    def on_duplicates(self):
        """显示重复文档"""
        if not self.db or not self.library_id:
            return

        from core.document import DocumentManager

        doc_manager = DocumentManager(self.db, self.library_id)
        docs = doc_manager.list_duplicates()

        self.document_area.load_documents(docs)
        self.status_bar.show_message(f"重复文档: {len(docs)} 个")


    def on_sidebar_refreshed(self):
        """侧边栏刷新后同步状态栏"""
        if self.library_id:
            from core.library import LibraryManager

            lib_manager = LibraryManager(self.db)
            stats = lib_manager.get_statistics(self.library_id)
            self.status_bar.set_info(
                f"共 {stats['total_documents']} 个文档  |  "
                f"未分类 {stats['uncategorized_documents']}  |  "
                f"重复 {stats['duplicate_documents']}"
            )
    def closeEvent(self, event):
        """关闭时保存窗口状态"""
        config = ConfigManager()
        geo = self.geometry()
        config.save_window_geometry(geo.x(), geo.y(), geo.width(), geo.height())

        if self.db:
            self.db.close()

        event.accept()
    def try_restore_last_library(self) -> bool:
        """尝试恢复上次打开的库"""
        config = ConfigManager()

        if not config.get("auto_open_last", True):
            return False

        last = config.get_last_library()
        if not last:
            return False

        try:
            self.open_library(last['id'], last['db_path'])
            return True
        except Exception as e:
            logger.warning(f"恢复上次库失败: {e}")
            return False

    def on_uncategorized(self):
        """显示未分类文档"""
        if not self.db or not self.library_id:
            return
        from core.document import DocumentManager
        doc_manager = DocumentManager(self.db, self.library_id)
        docs = doc_manager.list_uncategorized()
        self.document_area.load_documents(docs)
        self.status_bar.show_message(f"未分类文档: {len(docs)} 个")

    def on_untagged(self):
        """显示未打标签文档"""
        if not self.db or not self.library_id:
            return
        from core.document import DocumentManager
        doc_manager = DocumentManager(self.db, self.library_id)
        docs = doc_manager.list_untagged()
        self.document_area.load_documents(docs)
        self.status_bar.show_message(f"未打标签文档: {len(docs)} 个")

    def on_duplicates(self):
        """显示重复文档"""
        if not self.db or not self.library_id:
            return
        from core.document import DocumentManager
        doc_manager = DocumentManager(self.db, self.library_id)
        docs = doc_manager.list_duplicates()
        self.document_area.load_documents(docs)
        self.status_bar.show_message(f"重复文档: {len(docs)} 个")

    def on_sidebar_refreshed(self):
        """侧边栏刷新后更新状态栏"""
        if not self.db or not self.library_id:
            return
        lib_manager = LibraryManager(self.db)
        stats = lib_manager.get_statistics(self.library_id)
        self.status_bar.set_info(
            f"共 {stats['total_documents']} 个文档  |  "
            f"未分类 {stats['uncategorized_documents']}  |  "
            f"重复 {stats['duplicate_documents']}"
        )