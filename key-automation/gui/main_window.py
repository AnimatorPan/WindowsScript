import json
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QComboBox, QLineEdit, QSpinBox, QCheckBox,
    QGroupBox, QMessageBox, QFileDialog, QInputDialog,
    QDialog, QFormLayout, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

sys.path.insert(0, '..')
from core.action import Action, ActionList
from core.executor import ActionExecutor
from core.preset import PresetManager


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.action_list = ActionList()
        self.executor = ActionExecutor(self.action_list)
        self.preset_manager = PresetManager()
        self.current_file = None
        
        self._setup_ui()
        self._connect_signals()
        self._update_ui_state()
        self._refresh_preset_list()
    
    def _setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("按键精灵自动化工具")
        self.setMinimumSize(700, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # === 预设区域 ===
        preset_group = QGroupBox("预设")
        preset_layout = QVBoxLayout(preset_group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(300)
        preset_layout.addWidget(self.preset_combo)
        
        # 预设操作按钮
        preset_btn_layout = QHBoxLayout()
        
        self.btn_load_preset = QPushButton("加载预设")
        self.btn_save_preset = QPushButton("保存当前为预设")
        self.btn_edit_preset = QPushButton("编辑预设")
        self.btn_delete_preset = QPushButton("删除预设")
        self.btn_import_preset = QPushButton("导入")
        self.btn_export_preset = QPushButton("导出")
        
        preset_btn_layout.addWidget(self.btn_load_preset)
        preset_btn_layout.addWidget(self.btn_save_preset)
        preset_btn_layout.addWidget(self.btn_edit_preset)
        preset_btn_layout.addWidget(self.btn_delete_preset)
        preset_btn_layout.addWidget(self.btn_import_preset)
        preset_btn_layout.addWidget(self.btn_export_preset)
        preset_btn_layout.addStretch()
        
        preset_layout.addLayout(preset_btn_layout)
        main_layout.addWidget(preset_group)
        
        # === 动作列表区域 ===
        list_group = QGroupBox("动作列表")
        list_layout = QVBoxLayout(list_group)
        
        self.action_list_widget = QListWidget()
        self.action_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        list_layout.addWidget(self.action_list_widget)
        
        # 列表操作按钮
        list_btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("添加")
        self.btn_delete = QPushButton("删除")
        self.btn_move_up = QPushButton("上移")
        self.btn_move_down = QPushButton("下移")
        self.btn_clear = QPushButton("清空")
        
        list_btn_layout.addWidget(self.btn_add)
        list_btn_layout.addWidget(self.btn_delete)
        list_btn_layout.addWidget(self.btn_move_up)
        list_btn_layout.addWidget(self.btn_move_down)
        list_btn_layout.addWidget(self.btn_clear)
        list_btn_layout.addStretch()
        
        list_layout.addLayout(list_btn_layout)
        main_layout.addWidget(list_group, stretch=2)
        
        # === 添加动作区域 ===
        add_group = QGroupBox("添加动作")
        add_layout = QVBoxLayout(add_group)
        
        # 第一行：类型和修饰键
        row1_layout = QHBoxLayout()
        
        # 动作类型
        row1_layout.addWidget(QLabel("类型:"))
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems(["按键", "按下", "释放", "鼠标点击", "鼠标移动", "延迟"])
        row1_layout.addWidget(self.action_type_combo)
        
        # 修饰键选择
        row1_layout.addWidget(QLabel("修饰键:"))
        self.modifier_ctrl = QCheckBox("Ctrl")
        self.modifier_shift = QCheckBox("Shift")
        self.modifier_alt = QCheckBox("Alt")
        self.modifier_win = QCheckBox("Win")
        row1_layout.addWidget(self.modifier_ctrl)
        row1_layout.addWidget(self.modifier_shift)
        row1_layout.addWidget(self.modifier_alt)
        row1_layout.addWidget(self.modifier_win)
        row1_layout.addStretch()
        
        add_layout.addLayout(row1_layout)
        
        # 第二行：值输入和延迟
        row2_layout = QHBoxLayout()
        
        # 值输入
        row2_layout.addWidget(QLabel("按键/坐标:"))
        self.action_value_input = QLineEdit()
        self.action_value_input.setPlaceholderText("如: f (组合键示例: Ctrl+Shift+f)")
        row2_layout.addWidget(self.action_value_input, stretch=1)
        
        # 延迟输入
        row2_layout.addWidget(QLabel("延迟(ms):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 60000)
        self.delay_spin.setValue(100)
        self.delay_spin.setSuffix(" ms")
        row2_layout.addWidget(self.delay_spin)
        
        # 添加按钮
        self.btn_add_action = QPushButton("添加到列表")
        row2_layout.addWidget(self.btn_add_action)
        
        add_layout.addLayout(row2_layout)
        
        # 帮助提示
        help_label = QLabel("支持: a-z, 0-9, F1-F12, 方向键(left/right/up/down), enter, space, tab, esc, ctrl, alt, shift, win...")
        help_label.setStyleSheet("color: gray; font-size: 11px;")
        add_layout.addWidget(help_label)
        
        main_layout.addWidget(add_group)
        
        # === 窗口设置区域 ===
        window_group = QGroupBox("窗口设置")
        window_layout = QHBoxLayout(window_group)
        
        # 自动切换窗口选项
        self.auto_switch_checkbox = QCheckBox("自动切换到前一个窗口")
        self.auto_switch_checkbox.setChecked(True)
        self.auto_switch_checkbox.setToolTip("执行时自动切换到按键精灵前面的那个窗口")
        window_layout.addWidget(self.auto_switch_checkbox)
        
        # 目标窗口显示
        window_layout.addWidget(QLabel("目标窗口:"))
        self.target_window_label = QLabel("未设置")
        self.target_window_label.setStyleSheet("color: blue;")
        window_layout.addWidget(self.target_window_label, stretch=1)
        
        # 刷新按钮
        self.btn_refresh_window = QPushButton("刷新")
        self.btn_refresh_window.setToolTip("刷新目标窗口信息")
        window_layout.addWidget(self.btn_refresh_window)
        
        main_layout.addWidget(window_group)
        
        # === 设置区域 ===
        settings_group = QGroupBox("执行设置")
        settings_layout = QHBoxLayout(settings_group)
        
        # 循环设置
        self.loop_checkbox = QCheckBox("循环执行")
        settings_layout.addWidget(self.loop_checkbox)
        
        settings_layout.addWidget(QLabel("次数:"))
        self.loop_count_spin = QSpinBox()
        self.loop_count_spin.setRange(1, 9999)
        self.loop_count_spin.setValue(1)
        self.loop_count_spin.setEnabled(False)
        settings_layout.addWidget(self.loop_count_spin)
        
        settings_layout.addWidget(QLabel("间隔(ms):"))
        self.loop_delay_spin = QSpinBox()
        self.loop_delay_spin.setRange(0, 60000)
        self.loop_delay_spin.setValue(0)
        self.loop_delay_spin.setSuffix(" ms")
        self.loop_delay_spin.setEnabled(False)
        settings_layout.addWidget(self.loop_delay_spin)
        
        settings_layout.addStretch()
        
        # 文件操作按钮
        self.btn_new = QPushButton("新建")
        self.btn_open = QPushButton("打开")
        self.btn_save = QPushButton("保存")
        
        settings_layout.addWidget(self.btn_new)
        settings_layout.addWidget(self.btn_open)
        settings_layout.addWidget(self.btn_save)
        
        main_layout.addWidget(settings_group)
        
        # === 控制按钮区域 ===
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
        
        self.btn_start = QPushButton("▶ 开始")
        self.btn_start.setStyleSheet("font-size: 14px; padding: 10px 30px;")
        
        self.btn_pause = QPushButton("⏸ 暂停")
        self.btn_pause.setStyleSheet("font-size: 14px; padding: 10px 30px;")
        self.btn_pause.setEnabled(False)
        
        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.setStyleSheet("font-size: 14px; padding: 10px 30px;")
        self.btn_stop.setEnabled(False)
        
        control_layout.addStretch()
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_stop)
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # === 状态栏 ===
        self.status_label = QLabel("状态: 就绪 | 动作数: 0")
        main_layout.addWidget(self.status_label)
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 列表操作
        self.btn_add.clicked.connect(self._on_add_clicked)
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        self.btn_move_up.clicked.connect(self._on_move_up_clicked)
        self.btn_move_down.clicked.connect(self._on_move_down_clicked)
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        
        # 列表选择变化
        self.action_list_widget.currentRowChanged.connect(self._on_selection_changed)
        self.action_list_widget.itemClicked.connect(self._on_selection_changed)
        
        # 添加动作
        self.btn_add_action.clicked.connect(self._on_add_action_clicked)
        self.action_type_combo.currentIndexChanged.connect(self._on_action_type_changed)
        
        # 循环设置
        self.loop_checkbox.stateChanged.connect(self._on_loop_changed)
        
        # 文件操作
        self.btn_new.clicked.connect(self._on_new_clicked)
        self.btn_open.clicked.connect(self._on_open_clicked)
        self.btn_save.clicked.connect(self._on_save_clicked)
        
        # 控制按钮
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        
        # 窗口设置
        self.auto_switch_checkbox.stateChanged.connect(self._on_auto_switch_changed)
        self.btn_refresh_window.clicked.connect(self._on_refresh_window_clicked)
        
        # 执行器信号
        self.executor.action_started.connect(self._on_action_started)
        self.executor.action_finished.connect(self._on_action_finished)
        self.executor.execution_paused.connect(self._on_execution_paused)
        self.executor.execution_resumed.connect(self._on_execution_resumed)
        self.executor.execution_stopped.connect(self._on_execution_stopped)
        self.executor.execution_completed.connect(self._on_execution_completed)
        self.executor.execution_error.connect(self._on_execution_error)
        self.executor.target_window_changed.connect(self._on_target_window_changed)
        
        # 预设操作
        self.btn_load_preset.clicked.connect(self._on_load_preset_clicked)
        self.btn_save_preset.clicked.connect(self._on_save_preset_clicked)
        self.btn_edit_preset.clicked.connect(self._on_edit_preset_clicked)
        self.btn_delete_preset.clicked.connect(self._on_delete_preset_clicked)
        self.btn_import_preset.clicked.connect(self._on_import_preset_clicked)
        self.btn_export_preset.clicked.connect(self._on_export_preset_clicked)
    
    def _update_ui_state(self):
        """更新UI状态"""
        count = len(self.action_list)
        self.status_label.setText(f"状态: {'运行中' if self.executor.is_running else '就绪'} | 动作数: {count}")
        
        # 更新按钮状态
        has_selection = self.action_list_widget.currentRow() >= 0
        self.btn_delete.setEnabled(has_selection and not self.executor.is_running)
        self.btn_move_up.setEnabled(has_selection and not self.executor.is_running)
        self.btn_move_down.setEnabled(has_selection and not self.executor.is_running)
        self.btn_clear.setEnabled(count > 0 and not self.executor.is_running)
        
        # 控制按钮状态
        if self.executor.is_running:
            if self.executor.is_paused:
                self.btn_start.setEnabled(False)
                self.btn_pause.setEnabled(True)
                self.btn_pause.setText("▶ 继续")
                self.btn_stop.setEnabled(True)
            else:
                self.btn_start.setEnabled(False)
                self.btn_pause.setEnabled(True)
                self.btn_pause.setText("⏸ 暂停")
                self.btn_stop.setEnabled(True)
        else:
            self.btn_start.setEnabled(count > 0)
            self.btn_pause.setEnabled(False)
            self.btn_pause.setText("⏸ 暂停")
            self.btn_stop.setEnabled(False)
    
    def _refresh_list(self):
        """刷新动作列表显示"""
        self.action_list_widget.clear()
        for i, action in enumerate(self.action_list):
            item = QListWidgetItem(f"{i+1}. {str(action)}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.action_list_widget.addItem(item)
        self._update_ui_state()
    
    def _on_selection_changed(self):
        """列表选择改变"""
        self._update_ui_state()
    
    def _on_add_clicked(self):
        """添加按钮点击"""
        self._on_add_action_clicked()
    
    def _on_delete_clicked(self):
        """删除按钮点击"""
        row = self.action_list_widget.currentRow()
        if row >= 0:
            self.action_list.remove_action(row)
            self._refresh_list()
    
    def _on_move_up_clicked(self):
        """上移按钮点击"""
        row = self.action_list_widget.currentRow()
        if row > 0:
            new_row = self.action_list.move_up(row)
            self._refresh_list()
            self.action_list_widget.setCurrentRow(new_row)
    
    def _on_move_down_clicked(self):
        """下移按钮点击"""
        row = self.action_list_widget.currentRow()
        if row >= 0 and row < len(self.action_list) - 1:
            new_row = self.action_list.move_down(row)
            self._refresh_list()
            self.action_list_widget.setCurrentRow(new_row)
    
    def _on_clear_clicked(self):
        """清空按钮点击"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有动作吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.action_list.clear()
            self._refresh_list()
    
    def _on_action_type_changed(self, index):
        """动作类型改变"""
        types = [Action.TYPE_KEY_PRESS, Action.TYPE_KEY_DOWN, Action.TYPE_KEY_UP,
                 Action.TYPE_MOUSE_CLICK, Action.TYPE_MOUSE_MOVE, Action.TYPE_DELAY]
        action_type = types[index] if index < len(types) else Action.TYPE_KEY_PRESS
        
        # 启用/禁用修饰键选择
        is_key_action = action_type in [Action.TYPE_KEY_PRESS, Action.TYPE_KEY_DOWN, Action.TYPE_KEY_UP]
        self.modifier_ctrl.setEnabled(is_key_action)
        self.modifier_shift.setEnabled(is_key_action)
        self.modifier_alt.setEnabled(is_key_action)
        self.modifier_win.setEnabled(is_key_action)
        
        if action_type == Action.TYPE_DELAY:
            self.action_value_input.setEnabled(False)
            self.action_value_input.setPlaceholderText("使用下方延迟设置")
        else:
            self.action_value_input.setEnabled(True)
            if action_type in [Action.TYPE_MOUSE_CLICK, Action.TYPE_MOUSE_MOVE]:
                self.action_value_input.setPlaceholderText("格式: x,y (如: 100,200)")
            else:
                self.action_value_input.setPlaceholderText("如: f, left, right, up, down, enter...")
    
    def _on_add_action_clicked(self):
        """添加动作按钮点击"""
        index = self.action_type_combo.currentIndex()
        types = [Action.TYPE_KEY_PRESS, Action.TYPE_KEY_DOWN, Action.TYPE_KEY_UP,
                 Action.TYPE_MOUSE_CLICK, Action.TYPE_MOUSE_MOVE, Action.TYPE_DELAY]
        
        if index >= len(types):
            return
        
        action_type = types[index]
        value = self.action_value_input.text().strip()
        delay = self.delay_spin.value()
        
        params = {}
        
        if action_type == Action.TYPE_DELAY:
            params = {'ms': delay}
        elif action_type in [Action.TYPE_KEY_PRESS, Action.TYPE_KEY_DOWN, Action.TYPE_KEY_UP]:
            if not value:
                QMessageBox.warning(self, "警告", "请输入按键值")
                return
            params = {'key': value}
            
            # 添加修饰键
            modifiers = []
            if self.modifier_ctrl.isChecked():
                modifiers.append('ctrl')
            if self.modifier_shift.isChecked():
                modifiers.append('shift')
            if self.modifier_alt.isChecked():
                modifiers.append('alt')
            if self.modifier_win.isChecked():
                modifiers.append('win')
            if modifiers:
                params['modifiers'] = modifiers
                
        elif action_type in [Action.TYPE_MOUSE_CLICK, Action.TYPE_MOUSE_MOVE]:
            if value:
                try:
                    parts = value.split(',')
                    if len(parts) == 2:
                        params['x'] = int(parts[0].strip())
                        params['y'] = int(parts[1].strip())
                except ValueError:
                    QMessageBox.warning(self, "警告", "坐标格式错误，请使用 x,y 格式")
                    return
            
            if action_type == Action.TYPE_MOUSE_CLICK:
                params['button'] = 'left'  # 默认左键
        
        action = Action(action_type, params)
        self.action_list.add_action(action)
        self._refresh_list()
        
        # 清空输入和修饰键选择
        self.action_value_input.clear()
        self.modifier_ctrl.setChecked(False)
        self.modifier_shift.setChecked(False)
        self.modifier_alt.setChecked(False)
        self.modifier_win.setChecked(False)
        
        # 滚动到底部
        self.action_list_widget.scrollToBottom()
        self.action_list_widget.setCurrentRow(len(self.action_list) - 1)
    
    def _on_loop_changed(self, state):
        """循环设置改变"""
        enabled = state == Qt.CheckState.Checked.value
        self.loop_count_spin.setEnabled(enabled)
        self.loop_delay_spin.setEnabled(enabled)
    
    def _on_new_clicked(self):
        """新建按钮点击"""
        if len(self.action_list) > 0:
            reply = QMessageBox.question(
                self, "确认", "当前有未保存的动作，确定要新建吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.action_list.clear()
        self.current_file = None
        self._refresh_list()
        self.setWindowTitle("按键精灵自动化工具")
    
    def _on_open_clicked(self):
        """打开按钮点击"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开脚本", "", "JSON文件 (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.action_list.from_list(data.get('actions', []))
                self.current_file = file_path
                self._refresh_list()
                self.setWindowTitle(f"按键精灵自动化工具 - {file_path}")
                QMessageBox.information(self, "成功", "脚本加载成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")
    
    def _on_save_clicked(self):
        """保存按钮点击"""
        if self.current_file:
            file_path = self.current_file
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存脚本", "", "JSON文件 (*.json)"
            )
        
        if file_path:
            try:
                data = {
                    'actions': self.action_list.to_list()
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                self.current_file = file_path
                self.setWindowTitle(f"按键精灵自动化工具 - {file_path}")
                QMessageBox.information(self, "成功", "脚本保存成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def _on_start_clicked(self):
        """开始按钮点击"""
        if len(self.action_list) == 0:
            QMessageBox.warning(self, "警告", "动作列表为空")
            return
        
        # 设置循环参数
        if self.loop_checkbox.isChecked():
            self.executor.set_loop(
                self.loop_count_spin.value(),
                self.loop_delay_spin.value()
            )
        else:
            self.executor.set_loop(1, 0)
        
        self.executor.start_execution()
        self._update_ui_state()
    
    def _on_pause_clicked(self):
        """暂停/继续按钮点击"""
        if self.executor.is_paused:
            self.executor.resume()
        else:
            self.executor.pause()
    
    def _on_stop_clicked(self):
        """停止按钮点击"""
        self.executor.stop()
    
    def _on_auto_switch_changed(self, state):
        """自动切换窗口选项改变"""
        enabled = state == Qt.CheckState.Checked.value
        self.executor.set_auto_switch_window(enabled)
        self.btn_refresh_window.setEnabled(enabled)
        if enabled:
            self._on_refresh_window_clicked()
        else:
            self.target_window_label.setText("未启用")
            self.target_window_label.setStyleSheet("color: gray;")
    
    def _on_refresh_window_clicked(self):
        """刷新目标窗口按钮点击"""
        try:
            from utils.window_helper import WindowHelper
            current_hwnd = WindowHelper.get_current_window()
            target_hwnd = WindowHelper.get_previous_window(exclude_hwnds=[current_hwnd])
            
            if target_hwnd:
                info = WindowHelper.get_window_info(target_hwnd)
                title = info['title'][:40] + "..." if len(info['title']) > 40 else info['title']
                self.target_window_label.setText(title)
                self.target_window_label.setStyleSheet("color: green;")
                self.target_window_label.setToolTip(f"完整标题: {info['title']}\n类名: {info['class']}")
            else:
                self.target_window_label.setText("未找到")
                self.target_window_label.setStyleSheet("color: red;")
        except Exception as e:
            self.target_window_label.setText(f"错误: {str(e)}")
            self.target_window_label.setStyleSheet("color: red;")
    
    def _on_target_window_changed(self, title):
        """目标窗口改变信号"""
        short_title = title[:40] + "..." if len(title) > 40 else title
        self.target_window_label.setText(short_title)
        self.target_window_label.setStyleSheet("color: green;")
    
    def _on_action_started(self, index):
        """动作开始信号"""
        # 高亮当前执行的动作
        for i in range(self.action_list_widget.count()):
            item = self.action_list_widget.item(i)
            if i == index:
                item.setBackground(QColor(100, 200, 100))
            else:
                item.setBackground(QColor(255, 255, 255))
        
        self.status_label.setText(f"状态: 运行中 | 当前: {index + 1}/{len(self.action_list)}")
    
    def _on_action_finished(self, index):
        """动作完成信号"""
        pass
    
    def _on_execution_paused(self):
        """执行暂停信号"""
        self._update_ui_state()
        self.status_label.setText(f"状态: 已暂停 | 动作数: {len(self.action_list)}")
    
    def _on_execution_resumed(self):
        """执行恢复信号"""
        self._update_ui_state()
    
    def _on_execution_stopped(self):
        """执行停止信号"""
        self._reset_list_highlight()
        self._update_ui_state()
        self.status_label.setText(f"状态: 已停止 | 动作数: {len(self.action_list)}")
    
    def _on_execution_completed(self):
        """执行完成信号"""
        self._reset_list_highlight()
        self._update_ui_state()
        self.status_label.setText(f"状态: 完成 | 动作数: {len(self.action_list)}")
        QMessageBox.information(self, "完成", "所有动作执行完毕")
    
    def _on_execution_error(self, error_msg):
        """执行错误信号"""
        self._reset_list_highlight()
        self._update_ui_state()
        QMessageBox.critical(self, "执行错误", error_msg)
    
    def _reset_list_highlight(self):
        """重置列表高亮"""
        for i in range(self.action_list_widget.count()):
            item = self.action_list_widget.item(i)
            item.setBackground(QColor(255, 255, 255))
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.executor.is_running:
            self.executor.stop()
            self.executor.wait(1000)
        event.accept()
    
    # ==================== 预设操作 ====================
    
    def _refresh_preset_list(self):
        """刷新预设列表"""
        self.preset_combo.clear()
        presets = self.preset_manager.get_all_presets()
        for i, preset in enumerate(presets):
            self.preset_combo.addItem(f"{preset.name}", i)
    
    def _on_load_preset_clicked(self):
        """加载预设按钮点击"""
        index = self.preset_combo.currentIndex()
        if index < 0:
            QMessageBox.warning(self, "警告", "请先选择一个预设")
            return
        
        preset = self.preset_manager.get_preset(index)
        if preset:
            # 清空当前列表
            self.action_list.clear()
            # 加载预设动作
            self.action_list.from_list(preset.actions)
            self._refresh_list()
            QMessageBox.information(self, "成功", f"已加载预设: {preset.name}")
    
    def _on_save_preset_clicked(self):
        """保存当前为预设按钮点击"""
        if len(self.action_list) == 0:
            QMessageBox.warning(self, "警告", "当前动作列表为空")
            return
        
        # 输入预设名称
        name, ok = QInputDialog.getText(self, "保存预设", "请输入预设名称:")
        if not ok or not name.strip():
            return
        
        # 输入描述（可选）
        description, ok = QInputDialog.getText(
            self, "预设描述", "请输入预设描述（可选）:",
            text=f"包含 {len(self.action_list)} 个动作"
        )
        
        # 保存预设
        actions = self.action_list.to_list()
        self.preset_manager.add_preset(name.strip(), actions, description if ok else "")
        self._refresh_preset_list()
        
        # 选中新添加的预设
        self.preset_combo.setCurrentIndex(self.preset_combo.count() - 1)
        QMessageBox.information(self, "成功", f"预设 '{name}' 已保存")
    
    def _on_edit_preset_clicked(self):
        """编辑预设按钮点击"""
        index = self.preset_combo.currentIndex()
        if index < 0:
            QMessageBox.warning(self, "警告", "请先选择一个预设")
            return
        
        preset = self.preset_manager.get_preset(index)
        if not preset:
            return
        
        # 编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑预设: {preset.name}")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # 名称输入
        name_edit = QLineEdit(preset.name)
        layout.addRow("名称:", name_edit)
        
        # 描述输入
        desc_edit = QLineEdit(preset.description)
        layout.addRow("描述:", desc_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_cancel = QPushButton("取消")
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)
        
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.preset_manager.update_preset(
                index,
                name=name_edit.text(),
                description=desc_edit.text()
            )
            self._refresh_preset_list()
            self.preset_combo.setCurrentIndex(index)
            QMessageBox.information(self, "成功", "预设已更新")
    
    def _on_delete_preset_clicked(self):
        """删除预设按钮点击"""
        index = self.preset_combo.currentIndex()
        if index < 0:
            QMessageBox.warning(self, "警告", "请先选择一个预设")
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
            self.preset_manager.remove_preset(index)
            self._refresh_preset_list()
            QMessageBox.information(self, "成功", "预设已删除")
    
    def _on_import_preset_clicked(self):
        """导入预设按钮点击"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入预设", "", "JSON文件 (*.json)"
        )
        if file_path:
            if self.preset_manager.import_preset(file_path):
                self._refresh_preset_list()
                QMessageBox.information(self, "成功", "预设导入成功")
            else:
                QMessageBox.critical(self, "错误", "预设导入失败")
    
    def _on_export_preset_clicked(self):
        """导出预设按钮点击"""
        index = self.preset_combo.currentIndex()
        if index < 0:
            QMessageBox.warning(self, "警告", "请先选择一个预设")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出预设", "", "JSON文件 (*.json)"
        )
        if file_path:
            if self.preset_manager.export_preset(index, file_path):
                QMessageBox.information(self, "成功", "预设导出成功")
            else:
                QMessageBox.critical(self, "错误", "预设导出失败")
