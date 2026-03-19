"""
图形界面模块
"""
import sys
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from .copier import FileCopier, CopyTask
from .config import get_config_manager, AppConfig


class CopyWorker(QThread):
    """后台复制工作线程"""
    progress_signal = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(object)
    
    def __init__(self, copier: FileCopier, tasks: List[CopyTask]):
        super().__init__()
        self.copier = copier
        self.tasks = tasks
        self.copier.set_progress_callback(self.on_progress)
    
    def on_progress(self, current: int, total: int, message: str):
        self.progress_signal.emit(current, total, message)
    
    def run(self):
        result = self.copier.execute_copy(self.tasks)
        self.finished_signal.emit(result)
    
    def cancel(self):
        self.copier.cancel()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件批量复制工具 v1.0")
        self.setMinimumSize(900, 700)
        
        self.copier: Optional[FileCopier] = None
        self.copy_tasks: List[CopyTask] = []
        self.worker: Optional[CopyWorker] = None
        
        # 图片格式列表（从截图中提取，已移除 .fbx 和 .obj）
        self.image_extensions = {
            '.gif', '.iff', '.tdi', '.jpg', '.jpeg', '.jpe', '.jpf', '.jpx', '.jp2',
            '.j2c', '.j2k', '.jpc', '.jps', '.pcx', '.pdf', '.raw', '.pxr', '.png',
            '.pbm', '.pgm', '.ppm', '.pnm', '.pfm', '.pam', '.sct', '.asd', '.glb',
            '.usd', '.usdz', '.usda', '.usdc', '.gltf', '.ply', '.stl',
            '.tga', '.vda', '.icb', '.vst', '.tif', '.tiff', '.webp', '.mpo'
        }
        self.ignore_image_formats = False
        
        # 初始化配置管理器
        self.config_manager = get_config_manager()
        self.config = self.config_manager.load()
        
        self._setup_ui()
        self._apply_styles()
        self._load_config()
    
    def _load_config(self):
        """加载配置文件中的设置"""
        # 恢复文件路径
        if self.config.source_path and Path(self.config.source_path).exists():
            self.source_edit.setText(self.config.source_path)
        if self.config.target_path and Path(self.config.target_path).exists():
            self.target_edit.setText(self.config.target_path)
        
        # 恢复设置选项
        self.ignore_image_check.setChecked(self.config.ignore_image_formats)
        self.compare_content_check.setChecked(self.config.compare_content)
        
        # 恢复窗口大小
        if self.config.window_width >= 900 and self.config.window_height >= 700:
            self.resize(self.config.window_width, self.config.window_height)
        
        # 记录日志
        if self.config.source_path or self.config.target_path:
            self._log("已恢复上次使用的路径")
    
    def closeEvent(self, event):
        """窗口关闭事件，保存配置"""
        # 保存当前路径
        self.config_manager.update_paths(
            source_path=self.source_edit.text().strip(),
            target_path=self.target_edit.text().strip()
        )
        
        # 保存设置选项
        self.config_manager.update_settings(
            ignore_image_formats=self.ignore_image_check.isChecked(),
            compare_content=self.compare_content_check.isChecked()
        )
        
        # 保存窗口大小
        self.config_manager.update_window_size(self.width(), self.height())
        
        # 写入配置文件
        self.config_manager.save()
        self._log("配置已保存")
        
        event.accept()
    
    def _setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("文件批量复制工具")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 说明文字
        desc_label = QLabel("从源文件夹复制同名同格式文件到目标文件夹（仅复制目标中已存在的文件）")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(desc_label)
        
        main_layout.addSpacing(10)
        
        # 文件夹选择区域
        folder_group = QGroupBox("文件夹选择")
        folder_layout = QVBoxLayout(folder_group)
        
        # 源文件夹
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("源文件夹(A):"))
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("选择包含源文件的文件夹...")
        source_layout.addWidget(self.source_edit)
        self.source_btn = QPushButton("浏览...")
        self.source_btn.clicked.connect(self._select_source)
        source_layout.addWidget(self.source_btn)
        folder_layout.addLayout(source_layout)
        
        # 目标文件夹
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("目标文件夹(B):"))
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("选择目标文件夹（将被覆盖）...")
        target_layout.addWidget(self.target_edit)
        self.target_btn = QPushButton("浏览...")
        self.target_btn.clicked.connect(self._select_target)
        target_layout.addWidget(self.target_btn)
        folder_layout.addLayout(target_layout)
        
        # 忽略图片格式选项
        self.ignore_image_check = QCheckBox("忽略图片格式文件（GIF/JPG/PNG/TIFF/WEBP等）")
        self.ignore_image_check.setChecked(False)
        self.ignore_image_check.stateChanged.connect(self._on_ignore_changed)
        folder_layout.addWidget(self.ignore_image_check)
        
        # 只复制有变化的文件选项
        self.compare_content_check = QCheckBox("只复制有变化的文件（自动对比文件内容）")
        self.compare_content_check.setChecked(True)
        self.compare_content_check.stateChanged.connect(self._on_compare_changed)
        folder_layout.addWidget(self.compare_content_check)
        
        main_layout.addWidget(folder_group)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("扫描文件")
        self.scan_btn.setMinimumHeight(40)
        self.scan_btn.clicked.connect(self._scan_files)
        button_layout.addWidget(self.scan_btn)
        
        self.start_btn = QPushButton("开始复制")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_copy)
        button_layout.addWidget(self.start_btn)
        
        main_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(25)
        main_layout.addWidget(self.progress_bar)
        
        # 统计信息
        self.stats_label = QLabel("就绪")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.stats_label)
        
        # 分割器（预览表格 + 日志）
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 预览表格
        preview_group = QGroupBox("待复制文件预览")
        preview_layout = QVBoxLayout(preview_group)
        
        # 添加统计标签
        self.duplicate_label = QLabel("")
        self.duplicate_label.setStyleSheet("color: #666; font-size: 12px;")
        preview_layout.addWidget(self.duplicate_label)
        
        # 添加选择提示标签
        self.selection_label = QLabel("提示：按住 Ctrl 或 Shift 可多选，右键点击可移除选中项")
        self.selection_label.setStyleSheet("color: #2196F3; font-size: 11px;")
        preview_layout.addWidget(self.selection_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(["", "文件名", "相对路径", "大小", "差异状态"])
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # 启用多选
        self.preview_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # 添加右键菜单
        self.preview_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.preview_table.customContextMenuRequested.connect(self._show_context_menu)
        
        preview_layout.addWidget(self.preview_table)
        
        # 添加移除按钮区域
        remove_layout = QHBoxLayout()
        self.remove_selected_btn = QPushButton("移除选中项")
        self.remove_selected_btn.setEnabled(False)
        self.remove_selected_btn.clicked.connect(self._remove_selected_items)
        remove_layout.addWidget(self.remove_selected_btn)
        
        self.clear_all_btn = QPushButton("清空列表")
        self.clear_all_btn.setEnabled(False)
        self.clear_all_btn.clicked.connect(self._clear_all_items)
        remove_layout.addWidget(self.clear_all_btn)
        
        remove_layout.addStretch()
        preview_layout.addLayout(remove_layout)
        
        # 连接选择变化信号
        self.preview_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        splitter.addWidget(preview_group)
        
        # 日志区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        splitter.addWidget(log_group)
        
        # 设置分割比例
        splitter.setSizes([300, 200])
        
        main_layout.addWidget(splitter, stretch=1)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #fafafa;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
            }
            QTableWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 5px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        # 复选框样式
        self.setStyleSheet(self.styleSheet() + """
            QCheckBox {
                spacing: 8px;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #999;
                background: white;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #4CAF50;
                background: #4CAF50;
                border-radius: 3px;
            }
        """)
    
    def _on_ignore_changed(self, state):
        """忽略图片格式选项变化"""
        self.ignore_image_formats = (state == Qt.CheckState.Checked.value)
        if self.ignore_image_formats:
            self._log(f"已启用：忽略图片格式文件（共 {len(self.image_extensions)} 种格式）")
        else:
            self._log("已禁用：忽略图片格式文件")
        
        # 如果已经扫描过，重新扫描
        if self.copy_tasks and self.source_edit.text() and self.target_edit.text():
            self._log("设置已更改，请重新扫描文件")
            self.copy_tasks.clear()
            self._update_preview_table()
            self.start_btn.setEnabled(False)
    
    def _on_compare_changed(self, state):
        """只复制有变化的文件选项变化"""
        compare_content = (state == Qt.CheckState.Checked.value)
        if compare_content:
            self._log("已启用：只复制有变化的文件（自动对比文件内容）")
        else:
            self._log("已禁用：将复制所有同名文件（不对比内容）")
        
        # 如果已经扫描过，重新扫描
        if self.copy_tasks and self.source_edit.text() and self.target_edit.text():
            self._log("设置已更改，请重新扫描文件")
            self.copy_tasks.clear()
            self._update_preview_table()
            self.start_btn.setEnabled(False)
    
    def _is_image_file(self, file_path: Path) -> bool:
        """检查是否为图片格式文件"""
        ext = file_path.suffix.lower()
        return ext in self.image_extensions
    
    def _select_source(self):
        """选择源文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择源文件夹")
        if folder:
            self.source_edit.setText(folder)
            self._log(f"已选择源文件夹: {folder}")
    
    def _select_target(self):
        """选择目标文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if folder:
            self.target_edit.setText(folder)
            self._log(f"已选择目标文件夹: {folder}")
    
    def _log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def _scan_files(self):
        """扫描文件"""
        source = self.source_edit.text().strip()
        target = self.target_edit.text().strip()
        
        if not source or not target:
            QMessageBox.warning(self, "警告", "请先选择源文件夹和目标文件夹！")
            return
        
        if not Path(source).exists():
            QMessageBox.warning(self, "警告", "源文件夹不存在！")
            return
        
        if not Path(target).exists():
            QMessageBox.warning(self, "警告", "目标文件夹不存在！")
            return
        
        if source == target:
            QMessageBox.warning(self, "警告", "源文件夹和目标文件夹不能相同！")
            return
        
        try:
            self.copier = FileCopier(source, target)
            self.copier.set_ignore_extensions(
                self.image_extensions if self.ignore_image_formats else set()
            )
            # 设置是否对比文件内容
            compare_content = self.compare_content_check.isChecked()
            self.copier.set_compare_content(compare_content)
            
            self.copy_tasks = self.copier.find_copy_tasks()
            
            # 如果启用了忽略图片格式，过滤掉图片文件
            if self.ignore_image_formats:
                original_count = len(self.copy_tasks)
                self.copy_tasks = [
                    task for task in self.copy_tasks 
                    if not self._is_image_file(task.source)
                ]
                filtered_count = original_count - len(self.copy_tasks)
                if filtered_count > 0:
                    self._log(f"已忽略 {filtered_count} 个图片格式文件")
            
            # 更新预览表格
            self._update_preview_table()
            
            # 获取预览信息
            preview = self.copier.get_preview_info(self.copy_tasks)
            
            # 统计去重信息和差异信息
            total_duplicates = sum(len(task.duplicate_sources) for task in self.copy_tasks)
            content_diff = sum(1 for task in self.copy_tasks if task.diff_type == "content")
            size_diff = sum(1 for task in self.copy_tasks if task.diff_type == "size")
            
            self._log(f"扫描完成: 找到 {preview['file_count']} 个需要复制的文件")
            if compare_content:
                if content_diff > 0:
                    self._log(f"  - {content_diff} 个文件内容不同")
                if size_diff > 0:
                    self._log(f"  - {size_diff} 个文件大小不同")
            if total_duplicates > 0:
                self._log(f"自动去重: {total_duplicates} 个重复文件（保留最新修改日期）")
            self._log(f"总大小: {preview['total_size']}")
            
            dup_text = f"，已去重 {total_duplicates} 个" if total_duplicates > 0 else ""
            diff_text = ""
            if compare_content and (content_diff > 0 or size_diff > 0):
                diff_text = f"（内容不同{content_diff}个，大小不同{size_diff}个）"
            self.stats_label.setText(
                f"找到 {preview['file_count']} 个文件{dup_text}{diff_text}，总大小 {preview['total_size']}"
            )
            
            if self.copy_tasks:
                self.start_btn.setEnabled(True)
            else:
                self._log("未找到同名同格式的文件！")
                self.stats_label.setText("未找到同名同格式的文件")
                self.start_btn.setEnabled(False)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"扫描失败: {str(e)}")
            self._log(f"扫描失败: {str(e)}")
    
    def _update_preview_table(self):
        """更新预览表格"""
        self.preview_table.setRowCount(len(self.copy_tasks))
        
        # 统计去重信息
        total_duplicates = sum(len(task.duplicate_sources) for task in self.copy_tasks)
        
        if total_duplicates > 0:
            self.duplicate_label.setText(f"⚠️ 发现 {total_duplicates} 个重复文件已自动去重（保留最新修改日期）")
            self.duplicate_label.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
        else:
            self.duplicate_label.setText("✓ 未发现重复文件")
            self.duplicate_label.setStyleSheet("color: #4caf50; font-size: 12px;")
        
        # 更新按钮状态
        has_items = len(self.copy_tasks) > 0
        self.clear_all_btn.setEnabled(has_items)
        
        for i, task in enumerate(self.copy_tasks):
            # 行号/序号
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_table.setItem(i, 0, num_item)
            
            # 文件名
            filename = task.source.name
            self.preview_table.setItem(i, 1, QTableWidgetItem(filename))
            
            # 相对路径
            self.preview_table.setItem(i, 2, QTableWidgetItem(task.relative_path))
            
            # 大小
            try:
                size = task.source.stat().st_size
                size_str = self._format_size(size)
                self.preview_table.setItem(i, 3, QTableWidgetItem(size_str))
            except:
                self.preview_table.setItem(i, 3, QTableWidgetItem("未知"))
            
            # 差异信息
            if task.diff_type == "content":
                diff_item = QTableWidgetItem("内容不同")
                diff_item.setForeground(Qt.GlobalColor.red)
                self.preview_table.setItem(i, 4, diff_item)
            elif task.diff_type == "size":
                diff_item = QTableWidgetItem("大小不同")
                diff_item.setForeground(Qt.GlobalColor.darkYellow)
                self.preview_table.setItem(i, 4, diff_item)
            else:
                self.preview_table.setItem(i, 4, QTableWidgetItem("-"))
        
        self.preview_table.resizeColumnsToContents()
    
    def _on_selection_changed(self):
        """选择变化时更新按钮状态"""
        has_selection = len(self.preview_table.selectedItems()) > 0
        self.remove_selected_btn.setEnabled(has_selection)
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        if not self.copy_tasks:
            return
        
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu()
        remove_action = menu.addAction("移除选中项")
        remove_all_action = menu.addAction("清空列表")
        menu.addSeparator()
        select_all_action = menu.addAction("全选")
        
        action = menu.exec(self.preview_table.viewport().mapToGlobal(position))
        
        if action == remove_action:
            self._remove_selected_items()
        elif action == remove_all_action:
            self._clear_all_items()
        elif action == select_all_action:
            self.preview_table.selectAll()
    
    def _remove_selected_items(self):
        """移除选中的项目"""
        selected_rows = set()
        for item in self.preview_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            return
        
        # 从后往前删除，避免索引变化
        for row in sorted(selected_rows, reverse=True):
            if 0 <= row < len(self.copy_tasks):
                task = self.copy_tasks[row]
                self._log(f"已移除: {task.source.name}")
                del self.copy_tasks[row]
        
        # 更新表格
        self._update_preview_table()
        
        # 更新统计
        self.stats_label.setText(f"剩余 {len(self.copy_tasks)} 个文件待复制")
        
        # 如果没有项目了，禁用开始按钮
        if not self.copy_tasks:
            self.start_btn.setEnabled(False)
    
    def _clear_all_items(self):
        """清空所有项目"""
        if not self.copy_tasks:
            return
        
        reply = QMessageBox.question(
            self,
            "确认清空",
            f"确定要清空所有 {len(self.copy_tasks)} 个文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.copy_tasks.clear()
            self._update_preview_table()
            self.start_btn.setEnabled(False)
            self._log("已清空所有待复制文件")
            self.stats_label.setText("列表已清空")
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def _start_copy(self):
        """开始复制"""
        if not self.copy_tasks:
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            "确认复制",
            f"确定要复制 {len(self.copy_tasks)} 个文件吗？\n目标文件将被覆盖！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 禁用按钮
        self.scan_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.source_btn.setEnabled(False)
        self.target_btn.setEnabled(False)
        
        # 重置进度条
        self.progress_bar.setMaximum(len(self.copy_tasks))
        self.progress_bar.setValue(0)
        
        self._log("开始复制...")
        
        # 启动工作线程
        self.worker = CopyWorker(self.copier, self.copy_tasks)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, current: int, total: int, message: str):
        """进度更新"""
        self.progress_bar.setValue(current)
        self.stats_label.setText(f"进度: {current}/{total} - {message}")
        self._log(message)
    
    def _on_finished(self, result):
        """复制完成"""
        # 恢复按钮
        self.scan_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.source_btn.setEnabled(True)
        self.target_btn.setEnabled(True)
        
        # 显示结果
        self._log(f"复制完成!")
        self._log(f"成功: {result.success} 个")
        self._log(f"失败: {result.failed} 个")
        
        if result.errors:
            self._log("错误详情:")
            for error in result.errors:
                self._log(f"  - {error}")
        
        self.stats_label.setText(
            f"完成! 成功: {result.success} 个, 失败: {result.failed} 个"
        )
        
        # 只有失败时才弹窗提示
        if result.failed > 0:
            QMessageBox.warning(
                self, 
                "完成", 
                f"复制完成，但有错误。\n成功: {result.success} 个\n失败: {result.failed} 个"
            )


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
