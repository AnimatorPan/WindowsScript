"""
主窗口UI - 调试版本
"""
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QSpinBox, QComboBox, QCheckBox, QGroupBox,
    QProgressBar, QTextEdit, QMessageBox, QDoubleSpinBox, QSplitter,
    QDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# 导入自定义模块
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from video_player import VideoPlayer
    from converter import GIFConverter, ConversionConfig, ConversionResult
    from presets import PresetManager, Preset
except ImportError:
    # 打包后的路径
    from video_to_gif.video_player import VideoPlayer
    from video_to_gif.converter import GIFConverter, ConversionConfig, ConversionResult
    from video_to_gif.presets import PresetManager, Preset


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.video_path = ""
        self.output_path = ""
        self.is_converting = False
        
        # 组件
        self.video_player = None
        self.converter = GIFConverter()
        self.preset_manager = PresetManager()
        
        self._setup_ui()
        self._apply_styles()
        self._load_presets()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("视频转GIF工具 v1.0")
        self.setMinimumSize(1000, 1100)
        
        # 启用拖拽
        self.setAcceptDrops(True)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === 文件选择区域 ===
        file_group = QGroupBox("视频文件")
        file_layout = QHBoxLayout()
        
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("选择或拖拽视频/GIF文件到此处...")
        self.video_path_edit.setReadOnly(True)
        file_layout.addWidget(self.video_path_edit)
        
        self.browse_video_btn = QPushButton("浏览...")
        self.browse_video_btn.clicked.connect(self._browse_video)
        file_layout.addWidget(self.browse_video_btn)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # === 分割器（视频预览 + 参数设置）===
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 视频预览区域
        self.video_player = VideoPlayer()
        self.video_player.duration_changed.connect(self._on_duration_changed)
        self.video_player.crop_changed.connect(self._on_crop_changed)
        splitter.addWidget(self.video_player)
        
        # 参数设置区域
        settings_widget = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # 时间范围
        time_group = QGroupBox("时间范围")
        time_layout = QHBoxLayout()
        
        time_layout.addWidget(QLabel("开始:"))
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setRange(0, 99999)
        self.start_time_spin.setDecimals(3)
        self.start_time_spin.setValue(0)
        self.start_time_spin.setSuffix(" 秒")
        self.start_time_spin.valueChanged.connect(self._on_start_time_changed)
        time_layout.addWidget(self.start_time_spin)
        
        time_layout.addWidget(QLabel("结束:"))
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setRange(0, 99999)
        self.end_time_spin.setDecimals(3)
        self.end_time_spin.setValue(0)
        self.end_time_spin.setSuffix(" 秒")
        self.end_time_spin.valueChanged.connect(self._on_end_time_changed)
        time_layout.addWidget(self.end_time_spin)
        
        time_layout.addStretch()
        
        time_group.setLayout(time_layout)
        settings_layout.addWidget(time_group)
        
        # 转换参数
        params_group = QGroupBox("转换参数")
        params_layout = QVBoxLayout()
        params_layout.setSpacing(5)
        params_layout.setContentsMargins(10, 10, 10, 10)
        
        # 第一行：裁切XY
        row1 = QHBoxLayout()
        row1.setSpacing(20)
        row1.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        row1.addWidget(QLabel("裁切X:"))
        self.crop_x_spin = QSpinBox()
        self.crop_x_spin.setRange(0, 99999)
        self.crop_x_spin.setSuffix(" px")
        self.crop_x_spin.setFixedWidth(150)
        self.crop_x_spin.valueChanged.connect(self._on_crop_value_changed)
        row1.addWidget(self.crop_x_spin)
        
        row1.addWidget(QLabel(" Y:"))
        self.crop_y_spin = QSpinBox()
        self.crop_y_spin.setRange(0, 99999)
        self.crop_y_spin.setSuffix(" px")
        self.crop_y_spin.setFixedWidth(80)
        self.crop_y_spin.valueChanged.connect(self._on_crop_value_changed)
        row1.addWidget(self.crop_y_spin)
        row1.addStretch()
        
        params_layout.addLayout(row1)
        
        # 第二行：裁切宽高
        row2 = QHBoxLayout()
        row2.setSpacing(20)
        row2.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        row2.addWidget(QLabel("裁切宽:"))
        self.crop_w_spin = QSpinBox()
        self.crop_w_spin.setRange(10, 99999)
        self.crop_w_spin.setSuffix(" px")
        self.crop_w_spin.setFixedWidth(80)
        self.crop_w_spin.valueChanged.connect(self._on_crop_value_changed)
        row2.addWidget(self.crop_w_spin)
        
        row2.addWidget(QLabel(" 高:"))
        self.crop_h_spin = QSpinBox()
        self.crop_h_spin.setRange(10, 99999)
        self.crop_h_spin.setSuffix(" px")
        self.crop_h_spin.setFixedWidth(80)
        self.crop_h_spin.valueChanged.connect(self._on_crop_value_changed)
        row2.addWidget(self.crop_h_spin)
        row2.addStretch()
        
        params_layout.addLayout(row2)
        
        # 第三行：输出缩放比例
        row3 = QHBoxLayout()
        row3.setSpacing(20)
        row3.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        row3.addWidget(QLabel("输出缩放:"))
        self.output_scale_spin = QSpinBox()
        self.output_scale_spin.setRange(10, 200)
        self.output_scale_spin.setValue(100)
        self.output_scale_spin.setSuffix(" %")
        self.output_scale_spin.setFixedWidth(80)
        self.output_scale_spin.valueChanged.connect(self._update_file_size_estimate)
        row3.addWidget(self.output_scale_spin)
        
        row3.addStretch()
        
        params_layout.addLayout(row3)
        
        # 第四行：其他参数
        row4 = QHBoxLayout()
        row4.setSpacing(20)
        row4.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        row4.addWidget(QLabel("帧率:"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["8 fps", "10 fps", "15 fps", "20 fps", "30 fps"])
        self.fps_combo.setCurrentIndex(2)
        self.fps_combo.setFixedWidth(80)
        self.fps_combo.currentIndexChanged.connect(self._update_file_size_estimate)
        row4.addWidget(self.fps_combo)
        
        row4.addWidget(QLabel(" 颜色:"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(["256色", "128色", "64色", "32色"])
        self.color_combo.setCurrentIndex(1)
        self.color_combo.setFixedWidth(80)
        self.color_combo.currentIndexChanged.connect(self._update_file_size_estimate)
        row4.addWidget(self.color_combo)
        
        row4.addWidget(QLabel(" 优化:"))
        self.optimization_combo = QComboBox()
        self.optimization_combo.addItems(["高质量", "标准", "压缩", "极致"])
        self.optimization_combo.setCurrentIndex(1)
        self.optimization_combo.setFixedWidth(80)
        self.optimization_combo.currentIndexChanged.connect(self._update_file_size_estimate)
        row4.addWidget(self.optimization_combo)
        
        self.file_size_label = QLabel("预估: -")
        row4.addWidget(self.file_size_label)
        row4.addStretch()
        
        params_layout.addLayout(row4)
        
        params_group.setLayout(params_layout)
        settings_layout.addWidget(params_group)
        
        # 输出路径
        output_path_group = QGroupBox("输出设置")
        output_path_layout = QHBoxLayout()
        
        output_path_layout.addWidget(QLabel("输出路径:"))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择GIF输出位置...")
        output_path_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton("浏览...")
        self.browse_output_btn.clicked.connect(self._browse_output)
        output_path_layout.addWidget(self.browse_output_btn)
        
        output_path_group.setLayout(output_path_layout)
        settings_layout.addWidget(output_path_group)
        
        # 预设区域
        preset_group = QGroupBox("预设")
        preset_layout = QHBoxLayout()
        
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(200)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        
        self.save_preset_btn = QPushButton("保存当前为预设")
        self.save_preset_btn.clicked.connect(self._save_preset)
        preset_layout.addWidget(self.save_preset_btn)
        
        self.delete_preset_btn = QPushButton("删除预设")
        self.delete_preset_btn.clicked.connect(self._delete_preset)
        preset_layout.addWidget(self.delete_preset_btn)
        
        preset_layout.addStretch()
        
        preset_group.setLayout(preset_layout)
        settings_layout.addWidget(preset_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        settings_layout.addWidget(self.progress_bar)
        
        # 转换按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setMinimumSize(120, 40)
        self.convert_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.convert_btn.clicked.connect(self._start_conversion)
        button_layout.addWidget(self.convert_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumSize(100, 40)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_conversion)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        settings_layout.addLayout(button_layout)
        
        # 日志区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        settings_layout.addWidget(log_group)
        
        # 添加伸展因子，让布局向下适配
        settings_layout.addStretch()
        
        settings_widget.setLayout(settings_layout)
        splitter.addWidget(settings_widget)
        
        # 设置分割比例 - 两个区域都可以自适应
        splitter.setSizes([400, 400])
        splitter.setStretchFactor(0, 1)  # 视频区域可伸展
        splitter.setStretchFactor(1, 1)  # 参数区域也可伸展
        
        main_layout.addWidget(splitter)
    
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
            QPushButton#cancel_btn {
                background-color: #f44336;
            }
            QPushButton#cancel_btn:hover {
                background-color: #da190b;
            }
            QLineEdit {
                padding: 8px 6px;
                min-height: 24px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QSpinBox, QDoubleSpinBox, QComboBox {
                padding: 2px 8px;
                min-height: 16px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                height: 25px;
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
        """)
        self.cancel_btn.setObjectName("cancel_btn")
    
    def _load_presets(self):
        """加载预设"""
        self.preset_combo.clear()
        presets = self.preset_manager.get_all_presets()
        for preset in presets:
            self.preset_combo.addItem(f"{preset.name} - {preset.description}")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if self._is_video_file(file_path):
                self._load_video(file_path)
            else:
                QMessageBox.warning(self, "警告", "不支持的文件格式")
    
    def _is_video_file(self, file_path: str) -> bool:
        """检查是否为视频或GIF文件"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.gif'}
        ext = Path(file_path).suffix.lower()
        return ext in video_extensions
    
    def _browse_video(self):
        """浏览视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频或GIF文件",
            "",
            "视频/GIF文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm *.m4v *.gif);;所有文件 (*.*)"
        )
        if file_path:
            self._load_video(file_path)
    
    def _load_video(self, file_path: str):
        """加载视频"""
        self.video_path = file_path
        self.video_path_edit.setText(file_path)
        
        # 设置默认输出路径
        output_path = str(Path(file_path).with_suffix('.gif'))
        self.output_path = output_path
        self.output_path_edit.setText(output_path)
        
        # 加载视频到播放器
        if self.video_player.load_video(file_path):
            self._log(f"已加载视频: {file_path}")
            self._update_file_size_estimate()
        else:
            QMessageBox.critical(self, "错误", "加载视频失败")
            self._log("加载视频失败")
    
    def _on_duration_changed(self, duration: float):
        """视频时长变化"""
        self.start_time_spin.setRange(0, duration)
        self.end_time_spin.setRange(0, duration)
        self.end_time_spin.setValue(duration)
    
    def _on_crop_changed(self, rect):
        """裁切区域变化"""
        # 同步裁切数值到输入框
        self.crop_x_spin.blockSignals(True)
        self.crop_y_spin.blockSignals(True)
        self.crop_w_spin.blockSignals(True)
        self.crop_h_spin.blockSignals(True)
        
        self.crop_x_spin.setValue(rect.x())
        self.crop_y_spin.setValue(rect.y())
        self.crop_w_spin.setValue(rect.width())
        self.crop_h_spin.setValue(rect.height())
        
        self.crop_x_spin.blockSignals(False)
        self.crop_y_spin.blockSignals(False)
        self.crop_w_spin.blockSignals(False)
        self.crop_h_spin.blockSignals(False)
        
        self._update_file_size_estimate()
    
    def _on_crop_value_changed(self):
        """裁切数值变化"""
        rect = self.video_player.get_crop_rect()
        rect.setX(self.crop_x_spin.value())
        rect.setY(self.crop_y_spin.value())
        rect.setWidth(self.crop_w_spin.value())
        rect.setHeight(self.crop_h_spin.value())
        self.video_player.set_crop_rect(rect)
        self._update_file_size_estimate()
    
    def _on_start_time_changed(self, value):
        """开始时间变化"""
        if value >= self.end_time_spin.value():
            self.end_time_spin.setValue(value + 1)
        self._update_file_size_estimate()
    
    def _on_end_time_changed(self, value):
        """结束时间变化"""
        if value <= self.start_time_spin.value():
            self.start_time_spin.setValue(value - 1)
        self._update_file_size_estimate()
    
    def _browse_output(self):
        """浏览输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存GIF文件",
            self.output_path,
            "GIF文件 (*.gif)"
        )
        if file_path:
            if not file_path.lower().endswith('.gif'):
                file_path += '.gif'
            self.output_path = file_path
            self.output_path_edit.setText(file_path)
    
    def _on_preset_changed(self, index):
        """预设变化"""
        preset = self.preset_manager.get_preset(index)
        if preset:
            # 应用预设参数
            fps_map = {8: 0, 10: 1, 12: 2, 15: 3, 20: 4, 24: 5, 30: 6}
            color_map = {256: 0, 128: 1, 64: 2, 32: 3}
            opt_map = {'high': 0, 'standard': 1, 'compressed': 2, 'extreme': 3}
            
            if preset.fps in fps_map:
                self.fps_combo.setCurrentIndex(fps_map[preset.fps])
            if preset.color_quality in color_map:
                self.color_combo.setCurrentIndex(color_map[preset.color_quality])
            if preset.optimization_level in opt_map:
                self.optimization_combo.setCurrentIndex(opt_map[preset.optimization_level])
            
            self.output_scale_spin.setValue(preset.output_scale)
            
            self._log(f"已加载预设: {preset.name}")
            self._update_file_size_estimate()
    
    def _save_preset(self):
        """保存当前为预设"""
        name, ok = QInputDialog.getText(self, "保存预设", "请输入预设名称:")
        if not ok or not name:
            return
        
        description, ok = QInputDialog.getText(
            self, "预设描述", "请输入预设描述（可选）:",
            text=f"自定义预设"
        )
        
        fps_text = self.fps_combo.currentText()
        fps = int(fps_text.split()[0])
        
        color_text = self.color_combo.currentText()
        color_quality = int(color_text.replace("色", ""))
        
        opt_map = {0: 'high', 1: 'standard', 2: 'compressed', 3: 'extreme'}
        optimization_level = opt_map.get(self.optimization_combo.currentIndex(), 'standard')
        
        preset = Preset(
            name=name,
            description=description if ok else "",
            fps=fps,
            color_quality=color_quality,
            optimization_level=optimization_level,
            output_scale=self.output_scale_spin.value()
        )
        
        if self.preset_manager.add_preset(preset):
            self._load_presets()
            # 选中新添加的预设
            self.preset_combo.setCurrentIndex(self.preset_combo.count() - 1)
            self._log(f"预设 '{name}' 已保存")
        else:
            QMessageBox.warning(self, "警告", "预设名称已存在")
    
    def _delete_preset(self):
        """删除预设"""
        index = self.preset_combo.currentIndex()
        if index < 0:
            return
        
        preset = self.preset_manager.get_preset(index)
        if not preset:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除预设 '{preset.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.preset_manager.remove_preset(index):
                self._load_presets()
                self._log(f"预设 '{preset.name}' 已删除")
            else:
                QMessageBox.warning(self, "警告", "默认预设不能删除")
    
    def _update_file_size_estimate(self):
        """更新文件大小预估"""
        if not self.video_path:
            return
        
        try:
            config = self._create_config()
            estimated_size = self.converter.estimate_file_size(config)
            size_str = self.converter.format_file_size(estimated_size)
            self.file_size_label.setText(f"预估大小: ~{size_str}")
        except:
            self.file_size_label.setText("预估大小: -")
    
    def _create_config(self) -> ConversionConfig:
        """创建转换配置"""
        fps_text = self.fps_combo.currentText()
        fps = int(fps_text.split()[0])
        
        color_text = self.color_combo.currentText()
        color_quality = int(color_text.replace("色", ""))
        
        opt_map = {0: 'high', 1: 'standard', 2: 'compressed', 3: 'extreme'}
        optimization_level = opt_map.get(self.optimization_combo.currentIndex(), 'standard')
        
        return ConversionConfig(
            video_path=self.video_path,
            output_path=self.output_path,
            start_time=self.start_time_spin.value(),
            end_time=self.end_time_spin.value(),
            crop_x=self.crop_x_spin.value(),
            crop_y=self.crop_y_spin.value(),
            crop_w=self.crop_w_spin.value(),
            crop_h=self.crop_h_spin.value(),
            output_scale=self.output_scale_spin.value(),
            fps=fps,
            color_quality=color_quality,
            optimization_level=optimization_level
        )
    
    def _start_conversion(self):
        """开始转换"""
        if not self.video_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return
        
        if not self.output_path:
            QMessageBox.warning(self, "警告", "请设置输出路径")
            return
        
        # 检查输出目录是否存在
        output_dir = Path(self.output_path).parent
        if not output_dir.exists():
            QMessageBox.warning(self, "警告", "输出目录不存在")
            return
        
        # 创建配置
        config = self._create_config()
        
        # 禁用UI
        self.is_converting = True
        self._set_ui_enabled(False)
        self.progress_bar.setValue(0)
        
        self._log("开始转换...")
        
        # 开始转换
        self.converter.convert(
            config,
            progress_callback=self._on_conversion_progress,
            finished_callback=self._on_conversion_finished
        )
    
    def _cancel_conversion(self):
        """取消转换"""
        self.converter.cancel()
        self.is_converting = False
        self._set_ui_enabled(True)
        self.progress_bar.setValue(0)
        self._log("转换已取消")
    
    def _on_conversion_progress(self, progress: int, message: str):
        """转换进度更新"""
        self.progress_bar.setValue(progress)
        if message:
            self._log(message)
    
    def _on_conversion_finished(self, result: ConversionResult):
        """转换完成"""
        self.is_converting = False
        self._set_ui_enabled(True)
        self.progress_bar.setValue(100 if result.success else 0)
        
        if result.success:
            size_str = self.converter.format_file_size(result.file_size)
            self._log(f"转换完成!")
            self._log(f"输出文件: {result.output_path}")
            self._log(f"文件大小: {size_str}")
            self._log(f"时长: {result.duration:.2f} 秒")
            
            QMessageBox.information(
                self,
                "完成",
                f"GIF转换完成!\n\n文件大小: {size_str}"
            )
        else:
            self._log(f"转换失败: {result.error_message}")
            QMessageBox.critical(self, "错误", f"转换失败:\n{result.error_message}")
    
    def _set_ui_enabled(self, enabled: bool):
        """设置UI启用状态"""
        self.convert_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(not enabled)
        self.browse_video_btn.setEnabled(enabled)
        self.browse_output_btn.setEnabled(enabled)
        self.save_preset_btn.setEnabled(enabled)
        self.delete_preset_btn.setEnabled(enabled)
        self.preset_combo.setEnabled(enabled)
        
        # 参数设置区域
        self.start_time_spin.setEnabled(enabled)
        self.end_time_spin.setEnabled(enabled)
        self.crop_x_spin.setEnabled(enabled)
        self.crop_y_spin.setEnabled(enabled)
        self.crop_w_spin.setEnabled(enabled)
        self.crop_h_spin.setEnabled(enabled)
        self.output_scale_spin.setEnabled(enabled)
        self.fps_combo.setEnabled(enabled)
        self.color_combo.setEnabled(enabled)
        self.optimization_combo.setEnabled(enabled)
    
    def _log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.is_converting:
            reply = QMessageBox.question(
                self,
                "确认",
                "转换正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self.converter.cancel()
        
        # 清理资源
        if self.video_player:
            self.video_player.cleanup()
        
        event.accept()
