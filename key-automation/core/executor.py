import time
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button
from .action import Action
import sys
import os

# 添加父目录到路径以导入utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.window_helper import WindowManager


class ActionExecutor(QThread):
    """后台执行线程"""
    
    action_started = pyqtSignal(int)
    action_finished = pyqtSignal(int)
    execution_paused = pyqtSignal()
    execution_resumed = pyqtSignal()
    execution_stopped = pyqtSignal()
    execution_completed = pyqtSignal()
    execution_error = pyqtSignal(str)
    target_window_changed = pyqtSignal(str)  # 目标窗口改变信号
    
    def __init__(self, action_list):
        super().__init__()
        self.action_list = action_list
        self._is_running = False
        self._is_paused = False
        self.current_index = 0
        self.loop_count = 1
        self.loop_delay = 0
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.window_manager = WindowManager()
        self._auto_switch_window = True  # 是否自动切换窗口
        
        # 线程同步
        self._mutex = QMutex()
        self._pause_condition = QWaitCondition()
    
    @property
    def is_running(self):
        with QMutexLocker(self._mutex):
            return self._is_running
    
    @property
    def is_paused(self):
        with QMutexLocker(self._mutex):
            return self._is_paused
    
    def set_loop(self, count=1, delay=0):
        """设置循环参数"""
        self.loop_count = max(1, count)
        self.loop_delay = max(0, delay)
    
    def set_auto_switch_window(self, enabled):
        """设置是否自动切换窗口"""
        self._auto_switch_window = enabled
    
    def start_execution(self):
        """开始执行"""
        with QMutexLocker(self._mutex):
            if not self._is_running:
                self._is_running = True
                self._is_paused = False
                self.current_index = 0
                
                # 保存当前窗口并激活目标窗口
                if self._auto_switch_window:
                    self.window_manager.save_current_window()
                    if self.window_manager.activate_target():
                        target_info = self.window_manager.get_target_info()
                        if target_info:
                            self.target_window_changed.emit(f"{target_info['title']}")
                        # 等待窗口完全激活
                        time.sleep(0.3)
                
                self.start()
    
    def pause(self):
        """暂停执行"""
        with QMutexLocker(self._mutex):
            if self._is_running and not self._is_paused:
                self._is_paused = True
        self.execution_paused.emit()
    
    def resume(self):
        """恢复执行"""
        with QMutexLocker(self._mutex):
            if self._is_running and self._is_paused:
                self._is_paused = False
                self._pause_condition.wakeAll()
        self.execution_resumed.emit()
    
    def stop(self):
        """停止执行"""
        with QMutexLocker(self._mutex):
            self._is_running = False
            self._is_paused = False
            self._pause_condition.wakeAll()
        self.execution_stopped.emit()
    
    def run(self):
        """执行线程主循环"""
        try:
            for loop in range(self.loop_count):
                # 检查是否停止
                with QMutexLocker(self._mutex):
                    if not self._is_running:
                        break
                
                self.current_index = 0
                
                while self.current_index < len(self.action_list.actions):
                    # 检查是否停止
                    with QMutexLocker(self._mutex):
                        if not self._is_running:
                            break
                    
                    # 暂停等待
                    with QMutexLocker(self._mutex):
                        while self._is_paused and self._is_running:
                            self._pause_condition.wait(self._mutex)
                    
                    # 再次检查是否停止
                    with QMutexLocker(self._mutex):
                        if not self._is_running:
                            break
                    
                    # 获取当前动作
                    action = self.action_list.get_action(self.current_index)
                    if action is None:
                        break
                    
                    # 发送动作开始信号
                    self.action_started.emit(self.current_index)
                    
                    # 执行动作
                    self._execute_action(action)
                    
                    # 发送动作完成信号
                    self.action_finished.emit(self.current_index)
                    
                    self.current_index += 1
                
                # 循环间隔（如果不是最后一次）
                if loop < self.loop_count - 1 and self.loop_delay > 0:
                    time.sleep(self.loop_delay / 1000.0)
            
            # 执行完成
            with QMutexLocker(self._mutex):
                if self._is_running:
                    self.execution_completed.emit()
            
        except Exception as e:
            self.execution_error.emit(str(e))
        finally:
            with QMutexLocker(self._mutex):
                self._is_running = False
                self._is_paused = False
            
            # 恢复原始窗口
            if self._auto_switch_window:
                self.window_manager.restore_original()
    
    def _execute_action(self, action):
        """执行单个动作"""
        try:
            if action.type == Action.TYPE_KEY_PRESS:
                self._press_key(action.params.get('key', ''), action.params.get('modifiers', []))
            
            elif action.type == Action.TYPE_KEY_DOWN:
                self._key_down(action.params.get('key', ''), action.params.get('modifiers', []))
            
            elif action.type == Action.TYPE_KEY_UP:
                self._key_up(action.params.get('key', ''), action.params.get('modifiers', []))
            
            elif action.type == Action.TYPE_MOUSE_CLICK:
                self._mouse_click(action.params)
            
            elif action.type == Action.TYPE_MOUSE_MOVE:
                self._mouse_move(action.params)
            
            elif action.type == Action.TYPE_DELAY:
                ms = action.params.get('ms', 0)
                time.sleep(ms / 1000.0)
        
        except Exception as e:
            raise Exception(f"执行动作失败 [{action}]: {str(e)}")
    
    def _press_key(self, key_str, modifiers=None):
        """按键，支持组合键"""
        modifiers = modifiers or []
        key = self._parse_key(key_str)
        mod_keys = [self._parse_key(m) for m in modifiers if self._parse_key(m)]
        
        if key:
            # 先按下修饰键（添加小延迟确保按键被注册）
            for mod_key in mod_keys:
                self.keyboard.press(mod_key)
                time.sleep(0.05)
            # 按下并释放主键
            time.sleep(0.05)
            self.keyboard.press(key)
            time.sleep(0.05)
            self.keyboard.release(key)
            time.sleep(0.05)
            # 释放修饰键（逆序）
            for mod_key in reversed(mod_keys):
                self.keyboard.release(mod_key)
                time.sleep(0.05)
    
    def _key_down(self, key_str, modifiers=None):
        """按下键，支持组合键"""
        modifiers = modifiers or []
        key = self._parse_key(key_str)
        mod_keys = [self._parse_key(m) for m in modifiers if self._parse_key(m)]
        
        if key:
            # 先按下修饰键
            for mod_key in mod_keys:
                self.keyboard.press(mod_key)
                time.sleep(0.05)
            # 按下主键
            time.sleep(0.05)
            self.keyboard.press(key)
    
    def _key_up(self, key_str, modifiers=None):
        """释放键，支持组合键"""
        modifiers = modifiers or []
        key = self._parse_key(key_str)
        mod_keys = [self._parse_key(m) for m in modifiers if self._parse_key(m)]
        
        if key:
            # 释放主键
            self.keyboard.release(key)
            time.sleep(0.05)
            # 释放修饰键（逆序）
            for mod_key in reversed(mod_keys):
                self.keyboard.release(mod_key)
                time.sleep(0.05)
    
    def _mouse_click(self, params):
        """鼠标点击"""
        button_str = params.get('button', 'left')
        x = params.get('x')
        y = params.get('y')
        
        # 移动到指定位置
        if x is not None and y is not None:
            self.mouse.position = (x, y)
        
        # 点击
        button = Button.left
        if button_str == 'right':
            button = Button.right
        elif button_str == 'middle':
            button = Button.middle
        
        self.mouse.click(button)
    
    def _mouse_move(self, params):
        """鼠标移动"""
        x = params.get('x', 0)
        y = params.get('y', 0)
        self.mouse.position = (x, y)
    
    def _parse_key(self, key_str):
        """解析键字符串"""
        if not key_str:
            return None
        
        key_str = key_str.lower().strip()
        
        # 特殊键映射
        special_keys = {
            'ctrl': Key.ctrl,
            'ctrl_l': Key.ctrl_l,
            'ctrl_r': Key.ctrl_r,
            'alt': Key.alt,
            'alt_l': Key.alt_l,
            'alt_r': Key.alt_r,
            'shift': Key.shift,
            'shift_l': Key.shift_l,
            'shift_r': Key.shift_r,
            'cmd': Key.cmd,
            'win': Key.cmd,
            'enter': Key.enter,
            'return': Key.enter,
            'space': Key.space,
            'tab': Key.tab,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'esc': Key.esc,
            'escape': Key.esc,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'home': Key.home,
            'end': Key.end,
            'pageup': Key.page_up,
            'pagedown': Key.page_down,
            'f1': Key.f1,
            'f2': Key.f2,
            'f3': Key.f3,
            'f4': Key.f4,
            'f5': Key.f5,
            'f6': Key.f6,
            'f7': Key.f7,
            'f8': Key.f8,
            'f9': Key.f9,
            'f10': Key.f10,
            'f11': Key.f11,
            'f12': Key.f12,
        }
        
        if key_str in special_keys:
            return special_keys[key_str]
        
        # 单字符键
        if len(key_str) == 1:
            return key_str
        
        return None


class QMutexLocker:
    """QMutex的上下文管理器"""
    def __init__(self, mutex):
        self._mutex = mutex
    
    def __enter__(self):
        self._mutex.lock()
        return self._mutex
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._mutex.unlock()
        return False
