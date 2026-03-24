"""
待整理中心 - 集中管理未分类、未标签、疑似重复的文档
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox,
    QComboBox, QWidget, QTabWidget, QGroupBox,
    QRadioButton, QButtonGroup, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import logging

logger = logging.getLogger(__name__)


class UnorganizedCenter(QDialog):
    """待整理中心对话框"""

    documents_organized = pyqtSignal()

    def __init__(self, db, library_id, parent=None):
        super().__init__(parent)

        self.db = db
        self.library_id = library_id
        self.unclassified_docs = []
        self.untagged_docs = []
        self.duplicate_groups = []

        self.setWindowTitle("待整理中心")
        self.setMinimumSize(1000, 700)

        self.init_ui()
        self.load_all_data()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        title_label = QLabel("待整理中心")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)

        self.tab_widget = QTabWidget()
        
        tab_uncategorized = self.create_uncategorized_tab()
        self.tab_widget.addTab(tab_uncategorized, "未分类文档")
        
        tab_untagged = self.create_untagged_tab()
        self.tab_widget.addTab(tab_untagged, "未标签文档")
        
        tab_duplicates = self.create_duplicates_tab()
        self.tab_widget.addTab(tab_duplicates, "疑似重复")
        
        layout.addWidget(self.tab_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_btn = QPushButton("刷新全部")
        refresh_btn.clicked.connect(self.load_all_data)
        button_layout.addWidget(refresh_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def create_uncategorized_tab(self):
        """创建未分类文档标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        desc_label = QLabel("以下文档尚未分配到任何分类，请为它们选择合适的分类")
        desc_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(desc_label)

        self.uncategorized_table = QTableWidget()
        self.uncategorized_table.setColumnCount(5)
        self.uncategorized_table.setHorizontalHeaderLabels(["文件名", "类型", "大小", "导入时间", "操作"])
        self.uncategorized_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.uncategorized_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.uncategorized_table.setAlternatingRowColors(True)
        layout.addWidget(self.uncategorized_table)

        self.uncategorized_stats = QLabel("加载中...")
        self.uncategorized_stats.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.uncategorized_stats)

        btn_layout = QHBoxLayout()
        self.batch_categorize_btn = QPushButton("批量分类")
        self.batch_categorize_btn.clicked.connect(self.batch_categorize)
        btn_layout.addWidget(self.batch_categorize_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def create_untagged_tab(self):
        """创建未标签文档标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        desc_label = QLabel("以下文档尚未添加任何标签，请为它们添加标签以便检索")
        desc_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(desc_label)

        self.untagged_table = QTableWidget()
        self.untagged_table.setColumnCount(5)
        self.untagged_table.setHorizontalHeaderLabels(["文件名", "类型", "大小", "导入时间", "操作"])
        self.untagged_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.untagged_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.untagged_table.setAlternatingRowColors(True)
        layout.addWidget(self.untagged_table)

        self.untagged_stats = QLabel("加载中...")
        self.untagged_stats.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.untagged_stats)

        btn_layout = QHBoxLayout()
        self.batch_tag_btn = QPushButton("批量标签")
        self.batch_tag_btn.clicked.connect(self.batch_tag)
        btn_layout.addWidget(self.batch_tag_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def create_duplicates_tab(self):
        """创建疑似重复标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        desc_label = QLabel("以下文档可能是重复的，请检查并决定保留哪些")
        desc_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(desc_label)

        self.duplicate_table = QTableWidget()
        self.duplicate_table.setColumnCount(6)
        self.duplicate_table.setHorizontalHeaderLabels([
            "选择", "文件名", "类型", "大小", "导入时间", "重复类型"
        ])
        self.duplicate_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.duplicate_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.duplicate_table.setAlternatingRowColors(True)
        layout.addWidget(self.duplicate_table)

        self.duplicate_stats = QLabel("加载中...")
        self.duplicate_stats.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.duplicate_stats)

        btn_layout = QHBoxLayout()
        
        self.handle_duplicates_btn = QPushButton("处理选中重复")
        self.handle_duplicates_btn.clicked.connect(self.handle_duplicates)
        btn_layout.addWidget(self.handle_duplicates_btn)
        
        self.ignore_duplicates_btn = QPushButton("忽略（标记为非重复）")
        self.ignore_duplicates_btn.clicked.connect(self.ignore_duplicates)
        btn_layout.addWidget(self.ignore_duplicates_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def load_all_data(self):
        """加载所有数据"""
        self.load_uncategorized_documents()
        self.load_untagged_documents()
        self.load_duplicate_documents()

    def load_uncategorized_documents(self):
        """加载未分类文档"""
        try:
            from core.document import DocumentManager

            doc_manager = DocumentManager(self.db, self.library_id)
            all_docs = doc_manager.list_all(limit=10000)
            self.unclassified_docs = []

            for doc in all_docs:
                doc_id = doc['id']
                categories = doc_manager.get_categories(doc_id)
                if len(categories) == 0:
                    self.unclassified_docs.append(doc)

            self.update_uncategorized_table()
            self.uncategorized_stats.setText(f"共 {len(self.unclassified_docs)} 个未分类文档")
            logger.info(f"加载未分类文档: {len(self.unclassified_docs)} 个")

        except Exception as e:
            logger.error(f"加载未分类文档失败: {e}")
            self.uncategorized_stats.setText("加载失败")

    def load_untagged_documents(self):
        """加载未标签文档"""
        try:
            from core.document import DocumentManager

            doc_manager = DocumentManager(self.db, self.library_id)
            all_docs = doc_manager.list_all(limit=10000)
            self.untagged_docs = []

            for doc in all_docs:
                doc_id = doc['id']
                tags = doc_manager.get_tags(doc_id)
                if len(tags) == 0:
                    self.untagged_docs.append(doc)

            self.update_untagged_table()
            self.untagged_stats.setText(f"共 {len(self.untagged_docs)} 个未标签文档")
            logger.info(f"加载未标签文档: {len(self.untagged_docs)} 个")

        except Exception as e:
            logger.error(f"加载未标签文档失败: {e}")
            self.untagged_stats.setText("加载失败")

    def load_duplicate_documents(self):
        """加载疑似重复文档"""
        try:
            from core.duplicate_detector import DuplicateDetector

            detector = DuplicateDetector(self.db, self.library_id)
            
            exact_groups = detector.find_exact_duplicates()
            similar_groups = detector.find_similar_by_name(similarity_threshold=0.85)
            
            self.duplicate_groups = []
            
            for group in exact_groups:
                for doc in group:
                    doc['duplicate_type'] = '完全重复'
                    doc['group_id'] = f"exact_{doc['file_hash']}"
                    self.duplicate_groups.append(doc)
            
            for group in similar_groups:
                for doc in group:
                    if not any(d['id'] == doc['id'] for d in self.duplicate_groups):
                        doc['duplicate_type'] = '文件名相似'
                        doc['group_id'] = f"similar_{id(group)}"
                        self.duplicate_groups.append(doc)

            self.update_duplicate_table()
            
            exact_count = sum(len(g) for g in exact_groups)
            similar_count = len(self.duplicate_groups) - exact_count
            self.duplicate_stats.setText(
                f"共 {len(self.duplicate_groups)} 个疑似重复文档 "
                f"(完全重复: {exact_count}, 文件名相似: {similar_count})"
            )
            logger.info(f"加载疑似重复文档: {len(self.duplicate_groups)} 个")

        except Exception as e:
            logger.error(f"加载疑似重复文档失败: {e}")
            self.duplicate_stats.setText("加载失败")

    def update_uncategorized_table(self):
        """更新未分类表格"""
        self.uncategorized_table.setRowCount(len(self.unclassified_docs))

        for row, doc in enumerate(self.unclassified_docs):
            name_item = QTableWidgetItem(doc['filename'])
            self.uncategorized_table.setItem(row, 0, name_item)

            type_item = QTableWidgetItem(doc.get('file_type', '未知'))
            self.uncategorized_table.setItem(row, 1, type_item)

            size = doc.get('file_size', 0)
            size_item = QTableWidgetItem(self.format_size(size))
            self.uncategorized_table.setItem(row, 2, size_item)

            date_item = QTableWidgetItem(str(doc.get('imported_at', '') or doc.get('import_date', '')))
            self.uncategorized_table.setItem(row, 3, date_item)

            action_item = QTableWidgetItem("双击分类")
            action_item.setForeground(QColor("#0066cc"))
            self.uncategorized_table.setItem(row, 4, action_item)

            for col in range(5):
                item = self.uncategorized_table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, doc['id'])

    def update_untagged_table(self):
        """更新未标签表格"""
        self.untagged_table.setRowCount(len(self.untagged_docs))

        for row, doc in enumerate(self.untagged_docs):
            name_item = QTableWidgetItem(doc['filename'])
            self.untagged_table.setItem(row, 0, name_item)

            type_item = QTableWidgetItem(doc.get('file_type', '未知'))
            self.untagged_table.setItem(row, 1, type_item)

            size = doc.get('file_size', 0)
            size_item = QTableWidgetItem(self.format_size(size))
            self.untagged_table.setItem(row, 2, size_item)

            date_item = QTableWidgetItem(str(doc.get('imported_at', '') or doc.get('import_date', '')))
            self.untagged_table.setItem(row, 3, date_item)

            action_item = QTableWidgetItem("双击标签")
            action_item.setForeground(QColor("#0066cc"))
            self.untagged_table.setItem(row, 4, action_item)

            for col in range(5):
                item = self.untagged_table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, doc['id'])

    def update_duplicate_table(self):
        """更新疑似重复表格"""
        self.duplicate_table.setRowCount(len(self.duplicate_groups))

        for row, doc in enumerate(self.duplicate_groups):
            check_item = QTableWidgetItem()
            check_item.setCheckState(Qt.CheckState.Unchecked)
            self.duplicate_table.setItem(row, 0, check_item)

            name_item = QTableWidgetItem(doc['filename'])
            self.duplicate_table.setItem(row, 1, name_item)

            type_item = QTableWidgetItem(doc.get('file_type', '未知'))
            self.duplicate_table.setItem(row, 2, type_item)

            size = doc.get('file_size', 0)
            size_item = QTableWidgetItem(self.format_size(size))
            self.duplicate_table.setItem(row, 3, size_item)

            date_item = QTableWidgetItem(str(doc.get('imported_at', '') or doc.get('import_date', '')))
            self.duplicate_table.setItem(row, 4, date_item)

            dup_type = doc.get('duplicate_type', '未知')
            type_item = QTableWidgetItem(dup_type)
            if dup_type == '完全重复':
                type_item.setBackground(QColor(180, 80, 80))
                type_item.setForeground(QColor(255, 220, 220))
            else:
                type_item.setBackground(QColor(180, 130, 80))
                type_item.setForeground(QColor(255, 240, 220))
            self.duplicate_table.setItem(row, 5, type_item)

            for col in range(1, 6):
                item = self.duplicate_table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, doc['id'])

    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def batch_categorize(self):
        """批量分类"""
        selected_rows = self.uncategorized_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要分类的文档")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        from core.category import CategoryManager
        
        try:
            cat_manager = CategoryManager(self.db, self.library_id)
            all_categories = cat_manager.list_all()
            
            if not all_categories:
                QMessageBox.warning(self, "提示", "没有可用的分类，请先创建分类")
                return
            
            cat_names = [c['name'] for c in all_categories]
            name, ok = QInputDialog.getItem(
                self, "批量分类", f"为 {len(selected_rows)} 个文档选择分类:", cat_names, 0, False
            )
            
            if ok and name:
                selected_cat = next((c for c in all_categories if c['name'] == name), None)
                if selected_cat:
                    success_count = 0
                    for index in selected_rows:
                        row = index.row()
                        item = self.uncategorized_table.item(row, 0)
                        if item:
                            doc_id = item.data(Qt.ItemDataRole.UserRole)
                            try:
                                cat_manager.add_document(selected_cat['id'], doc_id)
                                success_count += 1
                            except Exception as e:
                                logger.error(f"添加分类失败: {doc_id}, {e}")
                    
                    self.load_all_data()
                    self.documents_organized.emit()
                    QMessageBox.information(self, "成功", f"已为 {success_count} 个文档添加分类")
        
        except Exception as e:
            logger.error(f"批量分类失败: {e}")
            QMessageBox.critical(self, "错误", f"批量分类失败: {str(e)}")

    def batch_tag(self):
        """批量标签"""
        selected_rows = self.untagged_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要打标签的文档")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        from core.tag import TagManager
        
        try:
            tag_manager = TagManager(self.db, self.library_id)
            all_tags = tag_manager.list_all()
            
            if not all_tags:
                name, ok = QInputDialog.getText(
                    self, "创建标签", f"为 {len(selected_rows)} 个文档创建新标签:"
                )
                if ok and name.strip():
                    tag_manager.create(name.strip())
                    self.load_all_data()
                    self.documents_organized.emit()
                    QMessageBox.information(self, "成功", f"已创建标签: {name}")
                return
            
            tag_names = [t['name'] for t in all_tags] + ["[创建新标签]"]
            name, ok = QInputDialog.getItem(
                self, "批量标签", f"为 {len(selected_rows)} 个文档选择标签:", tag_names, 0, False
            )
            
            if ok and name:
                if name == "[创建新标签]":
                    new_name, ok2 = QInputDialog.getText(self, "创建标签", "输入新标签名称:")
                    if ok2 and new_name.strip():
                        tag_manager.create(new_name.strip())
                        self.load_all_data()
                        self.documents_organized.emit()
                        QMessageBox.information(self, "成功", f"已创建标签: {new_name}")
                else:
                    selected_tag = next((t for t in all_tags if t['name'] == name), None)
                    if selected_tag:
                        success_count = 0
                        for index in selected_rows:
                            row = index.row()
                            item = self.untagged_table.item(row, 0)
                            if item:
                                doc_id = item.data(Qt.ItemDataRole.UserRole)
                                try:
                                    tag_manager.add_to_document(selected_tag['id'], doc_id)
                                    success_count += 1
                                except Exception as e:
                                    logger.error(f"添加标签失败: {doc_id}, {e}")
                        
                        self.load_all_data()
                        self.documents_organized.emit()
                        QMessageBox.information(self, "成功", f"已为 {success_count} 个文档添加标签")
        
        except Exception as e:
            logger.error(f"批量标签失败: {e}")
            QMessageBox.critical(self, "错误", f"批量标签失败: {str(e)}")

    def handle_duplicates(self):
        """处理选中的重复文档"""
        selected_docs = []
        for row in range(self.duplicate_table.rowCount()):
            check_item = self.duplicate_table.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                name_item = self.duplicate_table.item(row, 1)
                if name_item:
                    doc_id = name_item.data(Qt.ItemDataRole.UserRole)
                    selected_docs.append(doc_id)
        
        if not selected_docs:
            QMessageBox.warning(self, "提示", "请先勾选要处理的重复文档")
            return
        
        from gui.dialogs.duplicate_handler_dialog import DuplicateHandlerDialog
        from core.duplicate_detector import DuplicateDetector
        
        try:
            detector = DuplicateDetector(self.db, self.library_id)
            all_groups = detector.find_exact_duplicates() + detector.find_similar_by_name()
            
            relevant_groups = []
            for group in all_groups:
                group_ids = [doc['id'] for doc in group]
                if any(doc_id in group_ids for doc_id in selected_docs):
                    relevant_groups.append(group)
            
            if not relevant_groups:
                QMessageBox.information(self, "提示", "未找到相关的重复组")
                return
            
            dialog = DuplicateHandlerDialog(self.db, self.library_id, relevant_groups, self)
            dialog.documents_updated.connect(self.load_all_data)
            dialog.documents_updated.connect(self.documents_organized.emit)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"处理重复文档失败: {e}")
            QMessageBox.critical(self, "错误", f"处理失败: {str(e)}")

    def ignore_duplicates(self):
        """忽略选中的重复文档（标记为非重复）"""
        selected_docs = []
        for row in range(self.duplicate_table.rowCount()):
            check_item = self.duplicate_table.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                name_item = self.duplicate_table.item(row, 1)
                if name_item:
                    doc_id = name_item.data(Qt.ItemDataRole.UserRole)
                    selected_docs.append(doc_id)
        
        if not selected_docs:
            QMessageBox.warning(self, "提示", "请先勾选要忽略的文档")
            return
        
        reply = QMessageBox.question(
            self, "确认", f"确定将 {len(selected_docs)} 个文档标记为非重复？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from core.duplicate_detector import DuplicateDetector
            detector = DuplicateDetector(self.db, self.library_id)
            
            for doc_id in selected_docs:
                detector.unmark_duplicate(doc_id)
            
            self.load_all_data()
            self.documents_organized.emit()
            QMessageBox.information(self, "成功", f"已将 {len(selected_docs)} 个文档标记为非重复")
