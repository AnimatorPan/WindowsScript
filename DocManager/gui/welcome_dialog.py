"""
欢迎对话框（完整版）
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path
import logging

from core.database import Database, create_database
from core.library import LibraryManager
from utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class WelcomeDialog(QDialog):
    """欢迎对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.selected_library = None
        self.config = ConfigManager()

        self.init_ui()
        self.load_recent_libraries()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("欢迎使用 DocManager")
        self.setModal(True)
        self.setMinimumSize(600, 450)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 标题
        title = QLabel("DocManager")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("文档管家 · 让文档管理更简单")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888; font-size: 11pt;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        create_btn = QPushButton("➕  创建新库")
        create_btn.setMinimumHeight(50)
        create_btn.setDefault(True)
        create_btn.clicked.connect(self.create_library)
        btn_layout.addWidget(create_btn)

        open_btn = QPushButton("📂  打开已有库")
        open_btn.setMinimumHeight(50)
        open_btn.clicked.connect(self.open_library)
        btn_layout.addWidget(open_btn)

        layout.addLayout(btn_layout)

        # 最近打开
        recent_label = QLabel("最近打开的库:")
        recent_label.setStyleSheet("color: #aaa; font-size: 9pt;")
        layout.addWidget(recent_label)

        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(160)
        self.recent_list.itemDoubleClicked.connect(self.on_recent_double_clicked)
        self.recent_list.itemClicked.connect(self.on_recent_single_clicked)
        layout.addWidget(self.recent_list)

        # 打开按钮行
        open_recent_layout = QHBoxLayout()
        self.open_recent_btn = QPushButton("打开选中")
        self.open_recent_btn.setEnabled(False)
        self.open_recent_btn.clicked.connect(self.open_selected_recent)
        open_recent_layout.addWidget(self.open_recent_btn)
        open_recent_layout.addStretch()
        layout.addLayout(open_recent_layout)

        layout.addStretch()

    def load_recent_libraries(self):
        """加载最近打开的库"""
        self.recent_list.clear()

        recent = self.config.get_recent_libraries()

        if not recent:
            item = QListWidgetItem("暂无最近打开的库")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(Qt.GlobalColor.gray)
            self.recent_list.addItem(item)
            return

        for lib in recent:
            name = lib.get("name", "未知库")
            db_path = lib.get("db_path", "")
            text = f"  {name}  —  {db_path}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, lib)
            item.setToolTip(db_path)
            self.recent_list.addItem(item)

    def on_recent_single_clicked(self, item: QListWidgetItem):
        """单击最近库"""
        lib = item.data(Qt.ItemDataRole.UserRole)
        self.open_recent_btn.setEnabled(lib is not None)

    def on_recent_double_clicked(self, item: QListWidgetItem):
        """双击最近库直接打开"""
        lib = item.data(Qt.ItemDataRole.UserRole)
        if lib:
            self._open_library_info(lib)

    def open_selected_recent(self):
        """打开选中的最近库"""
        current = self.recent_list.currentItem()
        if current:
            lib = current.data(Qt.ItemDataRole.UserRole)
            if lib:
                self._open_library_info(lib)

    def create_library(self):
        """创建新库"""
        from gui.dialogs.create_library_dialog import CreateLibraryDialog

        dialog = CreateLibraryDialog(self)
        if dialog.exec():
            info = dialog.get_library_info()

            try:
                storage_path = Path(info['storage_path'])
                storage_path.mkdir(parents=True, exist_ok=True)

                db_path = storage_path / f"{info['name']}.db"
                db = create_database(str(db_path))

                lib_manager = LibraryManager(db)
                library_id = lib_manager.create(
                    info['name'],
                    str(storage_path),
                    info.get('description', '')
                )
                db.close()

                self.selected_library = {
                    'id': library_id,
                    'name': info['name'],
                    'db_path': str(db_path),
                    'storage_path': str(storage_path)
                }

                # 记录到最近打开
                self.config.add_recent_library(
                    library_id, info['name'], str(db_path)
                )

                self.accept()

            except Exception as e:
                logger.error(f"创建库失败: {e}", exc_info=True)
                QMessageBox.critical(self, "错误", f"创建库失败:\n\n{str(e)}")

    def open_library(self):
        """打开已有库"""
        db_path, _ = QFileDialog.getOpenFileName(
            self, "选择库文件", "", "数据库文件 (*.db);;所有文件 (*.*)"
        )

        if db_path:
            try:
                db = Database(db_path)
                db.connect()

                lib_manager = LibraryManager(db)
                libraries = lib_manager.list_all()

                if not libraries:
                    QMessageBox.warning(self, "提示", "数据库中没有库记录")
                    db.close()
                    return

                library = libraries[0]
                db.close()

                self._open_library_info({
                    'id': library['id'],
                    'name': library['name'],
                    'db_path': db_path,
                    'storage_path': library['storage_path']
                })

            except Exception as e:
                logger.error(f"打开库失败: {e}", exc_info=True)
                QMessageBox.critical(self, "错误", f"打开库失败:\n\n{str(e)}")

    def _open_library_info(self, lib: dict):
        """内部：设置选中库并关闭对话框"""
        self.selected_library = lib

        # 记录到最近打开
        self.config.add_recent_library(
            lib['id'], lib['name'], lib['db_path']
        )

        self.accept()

    def get_selected_library(self):
        """获取选中的库"""
        return self.selected_library