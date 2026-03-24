"""
系统设置对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QFormLayout, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QSpinBox, QGroupBox,
    QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """系统设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_window = parent
        self.config_file = Path.home() / ".docmanager" / "config.json"
        self.settings = self.load_settings()
        
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("系统设置")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # 标签页
        tabs = QTabWidget()
        
        # 通用设置
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "通用")
        
        # 导入设置
        import_tab = self.create_import_tab()
        tabs.addTab(import_tab, "导入")
        
        # 显示设置
        display_tab = self.create_display_tab()
        tabs.addTab(display_tab, "显示")
        
        # 高级设置
        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, "高级")
        
        layout.addWidget(tabs)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def create_general_tab(self):
        """创建通用设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 语言设置
        lang_group = QGroupBox("语言")
        lang_layout = QFormLayout(lang_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        self.language_combo.setEnabled(False)  # 暂不支持
        lang_layout.addRow("界面语言:", self.language_combo)
        
        layout.addWidget(lang_group)
        
        # 主题设置
        theme_group = QGroupBox("主题")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["深色主题", "浅色主题"])
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        theme_layout.addRow("界面主题:", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # 启动设置
        startup_group = QGroupBox("启动")
        startup_layout = QVBoxLayout(startup_group)
        
        self.auto_open_last = QCheckBox("启动时自动打开上次的库")
        startup_layout.addWidget(self.auto_open_last)
        
        self.check_updates = QCheckBox("启动时检查更新")
        self.check_updates.setEnabled(False)  # 暂不支持
        startup_layout.addWidget(self.check_updates)
        
        layout.addWidget(startup_group)
        
        layout.addStretch()
        
        return widget
    
    def create_import_tab(self):
        """创建导入设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 导入行为
        behavior_group = QGroupBox("导入行为")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.copy_to_storage = QCheckBox("将文件复制到库存储目录")
        self.copy_to_storage.setChecked(True)
        behavior_layout.addWidget(self.copy_to_storage)
        
        self.check_duplicate = QCheckBox("导入时检查重复文件")
        self.check_duplicate.setChecked(True)
        behavior_layout.addWidget(self.check_duplicate)
        
        self.auto_categorize = QCheckBox("根据文件类型自动分类")
        behavior_layout.addWidget(self.auto_categorize)
        
        layout.addWidget(behavior_group)
        
        # 文件类型过滤
        filter_group = QGroupBox("文件类型过滤")
        filter_layout = QFormLayout(filter_group)
        
        self.allowed_types = QLineEdit()
        self.allowed_types.setPlaceholderText("留空表示允许所有类型")
        filter_layout.addRow("允许的类型:", self.allowed_types)
        
        self.excluded_types = QLineEdit()
        self.excluded_types.setPlaceholderText("例如: exe,dll,sys")
        filter_layout.addRow("排除的类型:", self.excluded_types)
        
        layout.addWidget(filter_group)
        
        # 大小限制
        size_group = QGroupBox("文件大小限制")
        size_layout = QFormLayout(size_group)
        
        self.max_file_size = QSpinBox()
        self.max_file_size.setRange(0, 10000)
        self.max_file_size.setSuffix(" MB")
        self.max_file_size.setValue(0)
        self.max_file_size.setSpecialValueText("无限制")
        size_layout.addRow("单个文件最大:", self.max_file_size)
        
        layout.addWidget(size_group)
        
        layout.addStretch()
        
        return widget
    
    def create_display_tab(self):
        """创建显示设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 列表显示
        list_group = QGroupBox("列表显示")
        list_layout = QFormLayout(list_group)
        
        self.items_per_page = QSpinBox()
        self.items_per_page.setRange(50, 1000)
        self.items_per_page.setSingleStep(50)
        self.items_per_page.setValue(500)
        list_layout.addRow("每页显示:", self.items_per_page)
        
        self.default_view = QComboBox()
        self.default_view.addItems(["列表视图", "网格视图"])
        list_layout.addRow("默认视图:", self.default_view)
        
        layout.addWidget(list_group)
        
        # 缩略图
        thumbnail_group = QGroupBox("缩略图")
        thumbnail_layout = QFormLayout(thumbnail_group)
        
        self.thumbnail_size = QSpinBox()
        self.thumbnail_size.setRange(64, 512)
        self.thumbnail_size.setSingleStep(32)
        self.thumbnail_size.setValue(128)
        self.thumbnail_size.setSuffix(" px")
        thumbnail_layout.addRow("缩略图大小:", self.thumbnail_size)
        
        self.generate_thumbnails = QCheckBox("自动生成缩略图")
        self.generate_thumbnails.setChecked(True)
        thumbnail_layout.addRow("", self.generate_thumbnails)
        
        layout.addWidget(thumbnail_group)
        
        # 预览
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.enable_preview = QCheckBox("启用文档预览")
        self.enable_preview.setChecked(True)
        preview_layout.addWidget(self.enable_preview)
        
        self.preview_pdf = QCheckBox("预览 PDF 文件（需要 PyMuPDF）")
        self.preview_pdf.setChecked(True)
        preview_layout.addWidget(self.preview_pdf)
        
        layout.addWidget(preview_group)
        
        layout.addStretch()
        
        return widget
    
    def create_advanced_tab(self):
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 数据库
        db_group = QGroupBox("数据库")
        db_layout = QVBoxLayout(db_group)
        
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(QLabel("数据库备份:"))
        backup_btn = QPushButton("立即备份")
        backup_btn.clicked.connect(self.backup_database)
        backup_layout.addWidget(backup_btn)
        backup_layout.addStretch()
        db_layout.addLayout(backup_layout)
        
        self.auto_backup = QCheckBox("每天自动备份")
        db_layout.addWidget(self.auto_backup)
        
        layout.addWidget(db_group)
        
        # 缓存
        cache_group = QGroupBox("缓存")
        cache_layout = QVBoxLayout(cache_group)
        
        cache_info = QLabel("缓存用于存储缩略图和预览数据")
        cache_info.setStyleSheet("color: #888;")
        cache_layout.addWidget(cache_info)
        
        clear_cache_btn = QPushButton("清除缓存")
        clear_cache_btn.clicked.connect(self.clear_cache)
        cache_layout.addWidget(clear_cache_btn)
        
        layout.addWidget(cache_group)
        
        # 日志
        log_group = QGroupBox("日志")
        log_layout = QFormLayout(log_group)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText("INFO")
        log_layout.addRow("日志级别:", self.log_level)
        
        log_btn_layout = QHBoxLayout()
        open_log_btn = QPushButton("打开日志文件")
        open_log_btn.clicked.connect(self.open_log_file)
        log_btn_layout.addWidget(open_log_btn)
        
        clear_log_btn = QPushButton("清除日志")
        clear_log_btn.clicked.connect(self.clear_log)
        log_btn_layout.addWidget(clear_log_btn)
        
        log_layout.addRow("", log_btn_layout)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        return widget
    
    def load_settings(self) -> dict:
        """加载设置"""
        default_settings = {
            'theme': 'dark',
            'language': 'zh_CN',
            'auto_open_last': True,
            'copy_to_storage': True,
            'check_duplicate': True,
            'auto_categorize': False,
            'items_per_page': 500,
            'default_view': 'list',
            'thumbnail_size': 128,
            'enable_preview': True,
            'log_level': 'INFO',
        }
        
        if not self.config_file.exists():
            return default_settings
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return {**default_settings, **settings}
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
            return default_settings
    
    def load_current_settings(self):
        """加载当前设置到界面"""
        # 通用
        if self.settings.get('theme') == 'light':
            self.theme_combo.setCurrentIndex(1)
        else:
            self.theme_combo.setCurrentIndex(0)
        
        self.auto_open_last.setChecked(self.settings.get('auto_open_last', True))
        
        # 导入
        self.copy_to_storage.setChecked(self.settings.get('copy_to_storage', True))
        self.check_duplicate.setChecked(self.settings.get('check_duplicate', True))
        self.auto_categorize.setChecked(self.settings.get('auto_categorize', False))
        
        # 显示
        self.items_per_page.setValue(self.settings.get('items_per_page', 500))
        
        if self.settings.get('default_view') == 'grid':
            self.default_view.setCurrentIndex(1)
        
        self.thumbnail_size.setValue(self.settings.get('thumbnail_size', 128))
        self.enable_preview.setChecked(self.settings.get('enable_preview', True))
        
        # 高级
        self.log_level.setCurrentText(self.settings.get('log_level', 'INFO'))
    
    def save_settings(self):
        """保存设置"""
        # 构建设置字典
        new_settings = {
            'theme': 'dark' if self.theme_combo.currentIndex() == 0 else 'light',
            'language': 'zh_CN',
            'auto_open_last': self.auto_open_last.isChecked(),
            'copy_to_storage': self.copy_to_storage.isChecked(),
            'check_duplicate': self.check_duplicate.isChecked(),
            'auto_categorize': self.auto_categorize.isChecked(),
            'items_per_page': self.items_per_page.value(),
            'default_view': 'list' if self.default_view.currentIndex() == 0 else 'grid',
            'thumbnail_size': self.thumbnail_size.value(),
            'enable_preview': self.enable_preview.isChecked(),
            'log_level': self.log_level.currentText(),
        }
        
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, indent=2, ensure_ascii=False)
            
            self.settings = new_settings
            
            QMessageBox.information(self, "成功", "设置已保存\n\n部分设置需要重启应用后生效")
            
            self.accept()
        
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败:\n\n{str(e)}")
    
    def on_theme_changed(self, index):
        """主题切换"""
        if not hasattr(self, 'main_window') or not self.main_window:
            return
        
        from utils.style_manager import StyleManager
        
        style_manager = StyleManager()
        
        if index == 0:  # 深色
            style_manager.load_theme(StyleManager.DARK_THEME)
        else:  # 浅色
            style_manager.load_theme(StyleManager.LIGHT_THEME)
    
    def backup_database(self):
        """备份数据库"""
        if not self.main_window or not self.main_window.db:
            QMessageBox.warning(self, "提示", "请先打开一个库")
            return
        
        backup_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存数据库备份",
            f"docmanager_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "数据库文件 (*.db)"
        )
        
        if backup_path:
            try:
                import shutil
                from pathlib import Path
                
                # 获取当前数据库路径
                db_path = self.main_window.current_library['db_path']
                
                # 复制数据库文件
                shutil.copy2(db_path, backup_path)
                
                QMessageBox.information(self, "成功", f"数据库已备份到:\n{backup_path}")
            
            except Exception as e:
                logger.error(f"备份数据库失败: {e}")
                QMessageBox.critical(self, "错误", f"备份失败:\n\n{str(e)}")
    
    def clear_cache(self):
        """清除缓存"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清除缓存吗？\n\n缩略图将被删除，下次查看时会重新生成。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: 实现缓存清理逻辑
            QMessageBox.information(self, "提示", "缓存清理功能开发中...")
    
    def open_log_file(self):
        """打开日志文件"""
        import os
        import platform
        
        log_file = Path("docmanager.log")
        
        if not log_file.exists():
            QMessageBox.warning(self, "提示", "日志文件不存在")
            return
        
        try:
            if platform.system() == 'Windows':
                os.startfile(str(log_file))
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{log_file}"')
            else:  # Linux
                os.system(f'xdg-open "{log_file}"')
        except Exception as e:
            logger.error(f"打开日志文件失败: {e}")
            QMessageBox.critical(self, "错误", f"打开失败:\n\n{str(e)}")
    
    def clear_log(self):
        """清除日志"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清除日志文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                log_file = Path("docmanager.log")
                if log_file.exists():
                    log_file.write_text("")
                    QMessageBox.information(self, "成功", "日志已清除")
            except Exception as e:
                logger.error(f"清除日志失败: {e}")
                QMessageBox.critical(self, "错误", f"清除失败:\n\n{str(e)}")