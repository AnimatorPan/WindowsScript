"""
侧边栏组件（完整集成版）
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton,
    QMenu, QMessageBox, QInputDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction, QColor, QIcon
import logging

logger = logging.getLogger(__name__)


class Sidebar(QWidget):
    """侧边栏"""

    # 信号
    all_documents_clicked = pyqtSignal()
    category_selected = pyqtSignal(int)
    tag_selected = pyqtSignal(int)
    smart_folder_selected = pyqtSignal(int)
    uncategorized_clicked = pyqtSignal()
    untagged_clicked = pyqtSignal()
    duplicates_clicked = pyqtSignal()
    sidebar_refreshed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_window = parent
        self.library_id = None

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setMinimumWidth(180)
        self.setMaximumWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 全部文档 ──────────────────────────
        all_btn = QPushButton("  📁  全部文档")
        all_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 12px;
                border: none;
                border-bottom: 1px solid #444;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4a4a4a; }
        """)
        all_btn.clicked.connect(self.all_documents_clicked)
        layout.addWidget(all_btn)

        # ── 待整理快捷入口 ────────────────────
        shortcut_group = self.create_shortcut_group()
        layout.addWidget(shortcut_group)

        # ── 分类 ──────────────────────────────
        cat_header = self.create_section_header("分类", self.add_category)
        layout.addWidget(cat_header)

        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.category_tree.itemClicked.connect(self.on_category_clicked)
        self.category_tree.customContextMenuRequested.connect(
            self.show_category_menu
        )
        self.category_tree.setMinimumHeight(120)
        layout.addWidget(self.category_tree)

        # ── 标签 ──────────────────────────────
        tag_header = self.create_section_header("标签", self.add_tag)
        layout.addWidget(tag_header)

        self.tag_tree = QTreeWidget()
        self.tag_tree.setHeaderHidden(True)
        self.tag_tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.tag_tree.itemClicked.connect(self.on_tag_clicked)
        self.tag_tree.customContextMenuRequested.connect(
            self.show_tag_menu
        )
        self.tag_tree.setMinimumHeight(100)
        layout.addWidget(self.tag_tree)

        # ── 智能文件夹 ────────────────────────
        sf_header = self.create_section_header("智能文件夹", self.add_smart_folder)
        layout.addWidget(sf_header)

        self.smart_folder_tree = QTreeWidget()
        self.smart_folder_tree.setHeaderHidden(True)
        self.smart_folder_tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.smart_folder_tree.itemClicked.connect(self.on_smart_folder_clicked)
        self.smart_folder_tree.customContextMenuRequested.connect(
            self.show_smart_folder_menu
        )
        self.smart_folder_tree.setMinimumHeight(80)
        layout.addWidget(self.smart_folder_tree)

        layout.addStretch()

    def create_section_header(self, title: str, add_callback) -> QWidget:
        """创建分区标题栏（带添加按钮）"""
        header = QWidget()
        header.setStyleSheet(
            "background-color: #383838; border-top: 1px solid #555;"
        )
        header.setFixedHeight(32)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 5, 0)

        label = QLabel(title)
        label.setStyleSheet(
            "font-size: 9pt; font-weight: bold; color: #aaa;"
            "background: transparent; border: none;"
        )
        layout.addWidget(label)
        layout.addStretch()

        add_btn = QPushButton("+")
        add_btn.setFixedSize(22, 22)
        add_btn.setToolTip(f"添加{title}")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaa;
                border: 1px solid #666;
                border-radius: 11px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0d7377;
                color: white;
                border-color: #0d7377;
            }
        """)
        add_btn.clicked.connect(add_callback)
        layout.addWidget(add_btn)

        return header

    def create_shortcut_group(self) -> QWidget:
        """创建待整理快捷入口"""
        group = QWidget()
        group.setStyleSheet("background-color: #333; border-bottom: 1px solid #444;")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        label = QLabel("快捷入口")
        label.setStyleSheet("font-size: 8pt; color: #888; border: none;")
        layout.addWidget(label)

        shortcuts = [
            ("⚠️  未分类", self.uncategorized_clicked),
            ("🏷️  未打标签", self.untagged_clicked),
            ("🔁  重复文档", self.duplicates_clicked),
        ]

        for text, signal in shortcuts:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                    font-size: 9pt;
                    color: #ccc;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
            """)
            btn.clicked.connect(signal)
            layout.addWidget(btn)

        return group

    # ──────────────────────────────────────────
    # 数据加载
    # ──────────────────────────────────────────

    def load_library(self, library_id: int):
        """加载库数据"""
        self.library_id = library_id
        self.load_categories()
        self.load_tags()
        self.load_smart_folders()

    def load_categories(self):
        """加载分类树"""
        self.category_tree.clear()

        if not self._check_db():
            return

        try:
            from core.category import CategoryManager

            cat_manager = CategoryManager(self.main_window.db, self.library_id)
            tree = cat_manager.get_tree()

            for cat in tree:
                self._add_category_item(None, cat, cat_manager)

            self.category_tree.expandAll()
            logger.info(f"加载分类完成")

        except Exception as e:
            logger.error(f"加载分类失败: {e}", exc_info=True)

    def _add_category_item(self, parent, category: dict, cat_manager):
        """递归添加分类节点"""
        count = cat_manager.get_document_count(category['id'])
        text = f"📂  {category['name']}  ({count})"

        if parent is None:
            item = QTreeWidgetItem(self.category_tree)
        else:
            item = QTreeWidgetItem(parent)

        item.setText(0, text)
        item.setData(0, Qt.ItemDataRole.UserRole, category['id'])
        item.setData(0, Qt.ItemDataRole.UserRole + 1, category['name'])

        for child in category.get('children', []):
            self._add_category_item(item, child, cat_manager)

    def load_tags(self):
        """加载标签树"""
        self.tag_tree.clear()

        if not self._check_db():
            return

        try:
            from core.tag import TagManager

            tag_manager = TagManager(self.main_window.db, self.library_id)
            tree = tag_manager.get_tree()

            for tag in tree:
                self._add_tag_item(None, tag, tag_manager)

            self.tag_tree.expandAll()
            logger.info(f"加载标签完成")

        except Exception as e:
            logger.error(f"加载标签失败: {e}", exc_info=True)

    def _add_tag_item(self, parent, tag: dict, tag_manager):
        """递归添加标签节点"""
        count = tag_manager.get_document_count(tag['id'])
        text = f"🏷️  {tag['name']}  ({count})"

        if parent is None:
            item = QTreeWidgetItem(self.tag_tree)
        else:
            item = QTreeWidgetItem(parent)

        item.setText(0, text)
        item.setData(0, Qt.ItemDataRole.UserRole, tag['id'])
        item.setData(0, Qt.ItemDataRole.UserRole + 1, tag['name'])

        # 设置颜色
        if tag.get('color'):
            item.setForeground(0, QColor(tag['color']))

        for child in tag.get('children', []):
            self._add_tag_item(item, child, tag_manager)

    def load_smart_folders(self):
        """加载智能文件夹"""
        self.smart_folder_tree.clear()

        if not self._check_db():
            return

        try:
            from core.smart_folder import SmartFolderManager

            sf_manager = SmartFolderManager(self.main_window.db, self.library_id)
            folders = sf_manager.list_all()

            for folder in folders:
                count = sf_manager.count_matches(folder['id'])
                enabled = folder['is_enabled']
                icon = "⚡" if enabled else "⏸"
                text = f"{icon}  {folder['name']}  ({count})"

                item = QTreeWidgetItem(self.smart_folder_tree)
                item.setText(0, text)
                item.setData(0, Qt.ItemDataRole.UserRole, folder['id'])
                item.setData(0, Qt.ItemDataRole.UserRole + 1, folder['name'])

                if not enabled:
                    item.setForeground(0, QColor("#888888"))

            logger.info(f"加载智能文件夹完成")

        except Exception as e:
            logger.error(f"加载智能文件夹失败: {e}", exc_info=True)

    # ──────────────────────────────────────────
    # 点击事件
    # ──────────────────────────────────────────

    def on_category_clicked(self, item: QTreeWidgetItem, column: int):
        """分类点击"""
        cat_id = item.data(0, Qt.ItemDataRole.UserRole)
        if cat_id:
            self.category_selected.emit(cat_id)

    def on_tag_clicked(self, item: QTreeWidgetItem, column: int):
        """标签点击"""
        tag_id = item.data(0, Qt.ItemDataRole.UserRole)
        if tag_id:
            self.tag_selected.emit(tag_id)

    def on_smart_folder_clicked(self, item: QTreeWidgetItem, column: int):
        """智能文件夹点击"""
        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        if folder_id:
            self.smart_folder_selected.emit(folder_id)

    # ──────────────────────────────────────────
    # 分类右键菜单
    # ──────────────────────────────────────────

    def show_category_menu(self, pos):
        """显示分类右键菜单"""
        item = self.category_tree.itemAt(pos)
        menu = QMenu(self)

        add_root_action = QAction("新建分类", self)
        add_root_action.triggered.connect(self.add_category)
        menu.addAction(add_root_action)

        if item:
            cat_id = item.data(0, Qt.ItemDataRole.UserRole)
            cat_name = item.data(0, Qt.ItemDataRole.UserRole + 1)

            add_sub_action = QAction(f"在 '{cat_name}' 下新建子分类", self)
            add_sub_action.triggered.connect(
                lambda: self.add_subcategory(cat_id, cat_name)
            )
            menu.addAction(add_sub_action)

            menu.addSeparator()

            rename_action = QAction("重命名", self)
            rename_action.triggered.connect(
                lambda: self.rename_category(cat_id, cat_name)
            )
            menu.addAction(rename_action)

            delete_action = QAction("删除", self)
            delete_action.triggered.connect(
                lambda: self.delete_category(cat_id, cat_name)
            )
            menu.addAction(delete_action)

        menu.exec(self.category_tree.viewport().mapToGlobal(pos))

    # ──────────────────────────────────────────
    # 标签右键菜单
    # ──────────────────────────────────────────

    def show_tag_menu(self, pos):
        """显示标签右键菜单"""
        item = self.tag_tree.itemAt(pos)
        menu = QMenu(self)

        add_action = QAction("新建标签", self)
        add_action.triggered.connect(self.add_tag)
        menu.addAction(add_action)

        if item:
            tag_id = item.data(0, Qt.ItemDataRole.UserRole)
            tag_name = item.data(0, Qt.ItemDataRole.UserRole + 1)

            add_sub_action = QAction(f"在 '{tag_name}' 下新建子标签", self)
            add_sub_action.triggered.connect(
                lambda: self.add_subtag(tag_id, tag_name)
            )
            menu.addAction(add_sub_action)

            menu.addSeparator()

            rename_action = QAction("重命名", self)
            rename_action.triggered.connect(
                lambda: self.rename_tag(tag_id, tag_name)
            )
            menu.addAction(rename_action)

            delete_action = QAction("删除", self)
            delete_action.triggered.connect(
                lambda: self.delete_tag(tag_id, tag_name)
            )
            menu.addAction(delete_action)

        menu.exec(self.tag_tree.viewport().mapToGlobal(pos))

    # ──────────────────────────────────────────
    # 智能文件夹右键菜单
    # ──────────────────────────────────────────

    def show_smart_folder_menu(self, pos):
        """显示智能文件夹右键菜单"""
        item = self.smart_folder_tree.itemAt(pos)
        menu = QMenu(self)

        add_action = QAction("新建智能文件夹", self)
        add_action.triggered.connect(self.add_smart_folder)
        menu.addAction(add_action)

        menu.addSeparator()

        preset_menu = menu.addMenu("创建预设")
        presets = [
            ("最近导入（7天）", "recent"),
            ("未分类文档", "uncategorized"),
            ("未打标签", "untagged"),
            ("重复文档", "duplicates"),
            ("大文件（>10MB）", "large_files"),
        ]
        for label, preset_type in presets:
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked, t=preset_type: self.add_preset_smart_folder(t)
            )
            preset_menu.addAction(action)

        if item:
            folder_id = item.data(0, Qt.ItemDataRole.UserRole)
            folder_name = item.data(0, Qt.ItemDataRole.UserRole + 1)

            menu.addSeparator()

            edit_action = QAction("编辑规则", self)
            edit_action.triggered.connect(
                lambda: self.edit_smart_folder(folder_id)
            )
            menu.addAction(edit_action)

            toggle_action = QAction("启用 / 禁用", self)
            toggle_action.triggered.connect(
                lambda: self.toggle_smart_folder(folder_id)
            )
            menu.addAction(toggle_action)

            delete_action = QAction("删除", self)
            delete_action.triggered.connect(
                lambda: self.delete_smart_folder(folder_id, folder_name)
            )
            menu.addAction(delete_action)

        menu.exec(self.smart_folder_tree.viewport().mapToGlobal(pos))

    # ──────────────────────────────────────────
    # 分类操作
    # ──────────────────────────────────────────

    def add_category(self):
        """新建根分类"""
        if not self._check_db():
            return

        name, ok = QInputDialog.getText(self, "新建分类", "分类名称:")
        if ok and name.strip():
            try:
                from core.category import CategoryManager

                cat_manager = CategoryManager(self.main_window.db, self.library_id)
                cat_manager.create(name.strip())
                self.load_categories()
                self.sidebar_refreshed.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建失败:\n{e}")

    def add_subcategory(self, parent_id: int, parent_name: str):
        """新建子分类"""
        if not self._check_db():
            return

        name, ok = QInputDialog.getText(
            self, "新建子分类", f"在 '{parent_name}' 下新建子分类名称:"
        )
        if ok and name.strip():
            try:
                from core.category import CategoryManager

                cat_manager = CategoryManager(self.main_window.db, self.library_id)
                cat_manager.create(name.strip(), parent_id=parent_id)
                self.load_categories()
                self.sidebar_refreshed.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建失败:\n{e}")

    def rename_category(self, cat_id: int, old_name: str):
        """重命名分类"""
        if not self._check_db():
            return

        name, ok = QInputDialog.getText(
            self, "重命名分类", "新名称:", text=old_name
        )
        if ok and name.strip():
            try:
                from core.category import CategoryManager

                cat_manager = CategoryManager(self.main_window.db, self.library_id)
                cat_manager.update(cat_id, name=name.strip())
                self.load_categories()
                self.sidebar_refreshed.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败:\n{e}")

    def delete_category(self, cat_id: int, cat_name: str):
        """删除分类"""
        if not self._check_db():
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除分类 '{cat_name}' 吗？\n\n子分类将提升到上级，文档不会被删除。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.category import CategoryManager

                cat_manager = CategoryManager(self.main_window.db, self.library_id)
                cat_manager.delete(cat_id, cascade=False)
                self.load_categories()
                self.sidebar_refreshed.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败:\n{e}")

    # ──────────────────────────────────────────
    # 标签操作
    # ──────────────────────────────────────────

    def add_tag(self):
        """新建标签"""
        if not self._check_db():
            return

        name, ok = QInputDialog.getText(self, "新建标签", "标签名称:")
        if ok and name.strip():
            try:
                from core.tag import TagManager

                tag_manager = TagManager(self.main_window.db, self.library_id)
                tag_manager.create(name.strip())
                self.load_tags()
                self.sidebar_refreshed.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建失败:\n{e}")

    def add_subtag(self, parent_id: int, parent_name: str):
        """新建子标签"""
        if not self._check_db():
            return

        name, ok = QInputDialog.getText(
            self, "新建子标签", f"在 '{parent_name}' 下新建子标签名称:"
        )
        if ok and name.strip():
            try:
                from core.tag import TagManager

                tag_manager = TagManager(self.main_window.db, self.library_id)
                tag_manager.create(name.strip(), parent_id=parent_id)
                self.load_tags()
                self.sidebar_refreshed.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建失败:\n{e}")

    def rename_tag(self, tag_id: int, old_name: str):
        """重命名标签"""
        if not self._check_db():
            return

        name, ok = QInputDialog.getText(
            self, "重命名标签", "新名称:", text=old_name
        )
        if ok and name.strip():
            try:
                from core.tag import TagManager

                tag_manager = TagManager(self.main_window.db, self.library_id)
                tag_manager.update(tag_id, name=name.strip())
                self.load_tags()
                self.sidebar_refreshed.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败:\n{e}")

    def delete_tag(self, tag_id: int, tag_name: str):
        """删除标签"""
        if not self._check_db():
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除标签 '{tag_name}' 吗？\n\n文档不会被删除，仅移除标签关联。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.tag import TagManager

                tag_manager = TagManager(self.main_window.db, self.library_id)
                tag_manager.delete(tag_id)
                self.load_tags()
                self.sidebar_refreshed.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败:\n{e}")

    # ──────────────────────────────────────────
    # 智能文件夹操作
    # ──────────────────────────────────────────

    def add_smart_folder(self):
        """新建智能文件夹"""
        if not self._check_db():
            return

        from gui.dialogs.smart_folder_dialog import SmartFolderDialog

        dialog = SmartFolderDialog(
            self.main_window.db, self.library_id, parent=self
        )
        if dialog.exec():
            self.load_smart_folders()
            self.sidebar_refreshed.emit()

    def add_preset_smart_folder(self, preset_type: str):
        """添加预设智能文件夹"""
        if not self._check_db():
            return

        try:
            from core.smart_folder import SmartFolderManager

            sf_manager = SmartFolderManager(self.main_window.db, self.library_id)
            sf_manager.create_preset_folder(preset_type)
            self.load_smart_folders()
            self.sidebar_refreshed.emit()
            QMessageBox.information(self, "成功", "预设智能文件夹创建成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建失败:\n{e}")

    def edit_smart_folder(self, folder_id: int):
        """编辑智能文件夹"""
        if not self._check_db():
            return

        from gui.dialogs.smart_folder_dialog import SmartFolderDialog

        dialog = SmartFolderDialog(
            self.main_window.db, self.library_id,
            folder_id=folder_id, parent=self
        )
        if dialog.exec():
            self.load_smart_folders()
            self.sidebar_refreshed.emit()

    def toggle_smart_folder(self, folder_id: int):
        """启用/禁用智能文件夹"""
        if not self._check_db():
            return

        try:
            from core.smart_folder import SmartFolderManager

            sf_manager = SmartFolderManager(self.main_window.db, self.library_id)
            folder = sf_manager.get(folder_id)

            if folder:
                new_state = not folder['is_enabled']
                sf_manager.update(folder_id, is_enabled=new_state)
                self.load_smart_folders()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"操作失败:\n{e}")

    def delete_smart_folder(self, folder_id: int, folder_name: str):
        """删除智能文件夹"""
        if not self._check_db():
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除智能文件夹 '{folder_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.smart_folder import SmartFolderManager

                sf_manager = SmartFolderManager(self.main_window.db, self.library_id)
                sf_manager.delete(folder_id)
                self.load_smart_folders()
                self.sidebar_refreshed.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败:\n{e}")

    # ──────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────

    def _check_db(self) -> bool:
        """检查数据库连接"""
        if not self.main_window or not self.main_window.db or not self.library_id:
            QMessageBox.warning(self, "提示", "请先打开一个库")
            return False
        return True

    def refresh_all(self):
        """刷新全部"""
        if self.library_id:
            self.load_categories()
            self.load_tags()
            self.load_smart_folders()