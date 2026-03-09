import win32gui
import win32con
import win32process
import ctypes
from ctypes import wintypes


class WindowHelper:
    """窗口操作辅助类"""
    
    @staticmethod
    def get_current_window():
        """获取当前活动窗口句柄"""
        return win32gui.GetForegroundWindow()
    
    @staticmethod
    def get_window_title(hwnd):
        """获取窗口标题"""
        if hwnd and win32gui.IsWindow(hwnd):
            return win32gui.GetWindowText(hwnd)
        return ""
    
    @staticmethod
    def get_window_class(hwnd):
        """获取窗口类名"""
        if hwnd and win32gui.IsWindow(hwnd):
            return win32gui.GetClassName(hwnd)
        return ""
    
    @staticmethod
    def get_window_info(hwnd):
        """获取窗口完整信息"""
        return {
            'hwnd': hwnd,
            'title': WindowHelper.get_window_title(hwnd),
            'class': WindowHelper.get_window_class(hwnd)
        }
    
    @staticmethod
    def set_foreground_window(hwnd):
        """将窗口设为前台窗口"""
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
        
        try:
            # 如果窗口被最小化，恢复它
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 将窗口带到前台
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False
    
    @staticmethod
    def enum_windows():
        """枚举所有可见窗口"""
        windows = []
        
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                windows.append(WindowHelper.get_window_info(hwnd))
            return True
        
        win32gui.EnumWindows(callback, None)
        return windows
    
    @staticmethod
    def find_window_by_title(title, partial_match=True):
        """根据标题查找窗口"""
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if partial_match:
                    if title.lower() in window_title.lower():
                        extra.append(hwnd)
                else:
                    if title == window_title:
                        extra.append(hwnd)
            return True
        
        result = []
        win32gui.EnumWindows(callback, result)
        return result[0] if result else None
    
    @staticmethod
    def get_previous_window(exclude_hwnds=None):
        """
        获取前一个活动窗口（排除当前窗口和指定句柄）
        
        Args:
            exclude_hwnds: 要排除的窗口句柄列表
        
        Returns:
            前一个窗口的句柄，如果没有则返回None
        """
        if exclude_hwnds is None:
            exclude_hwnds = []
        
        # 获取当前前台窗口
        current_hwnd = win32gui.GetForegroundWindow()
        
        # 获取所有窗口的Z序
        all_windows = []
        
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                all_windows.append(hwnd)
            return True
        
        win32gui.EnumWindows(callback, None)
        
        # 找到当前窗口的位置，返回它后面的第一个有效窗口
        found_current = False
        for hwnd in all_windows:
            if hwnd == current_hwnd:
                found_current = True
                continue
            
            if found_current and hwnd not in exclude_hwnds:
                # 确保窗口不是最小化的
                if not win32gui.IsIconic(hwnd):
                    return hwnd
        
        # 如果没找到，尝试获取任务栏上的上一个窗口
        return WindowHelper._get_last_active_window()
    
    @staticmethod
    def _get_last_active_window():
        """通过Windows API获取上一个活动窗口"""
        try:
            # 使用GetWindow获取前一个窗口
            current = win32gui.GetForegroundWindow()
            prev = win32gui.GetWindow(current, win32con.GW_HWNDPREV)
            
            while prev and win32gui.IsWindow(prev):
                if win32gui.IsWindowVisible(prev) and not win32gui.IsIconic(prev):
                    if win32gui.GetWindowText(prev):
                        return prev
                prev = win32gui.GetWindow(prev, win32con.GW_HWNDPREV)
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_window_thread_process_id(hwnd):
        """获取窗口的线程ID和进程ID"""
        if hwnd and win32gui.IsWindow(hwnd):
            return win32process.GetWindowThreadProcessId(hwnd)
        return (0, 0)
    
    @staticmethod
    def attach_thread_input(hwnd):
        """附加线程输入（用于跨线程设置前台窗口）"""
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
            foreground_thread = win32process.GetWindowThreadProcessId(foreground_hwnd)[0]
            target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
            
            if foreground_thread != target_thread:
                # 附加线程输入
                ctypes.windll.user32.AttachThreadInput(foreground_thread, target_thread, True)
                return foreground_thread, target_thread
            return None
        except Exception:
            return None
    
    @staticmethod
    def detach_thread_input(threads):
        """分离线程输入"""
        if threads:
            try:
                foreground_thread, target_thread = threads
                ctypes.windll.user32.AttachThreadInput(foreground_thread, target_thread, False)
            except Exception:
                pass


class WindowManager:
    """窗口管理器，用于保存和恢复窗口状态"""
    
    def __init__(self):
        self._original_window = None
        self._target_window = None
        self._attached_threads = None
    
    def save_current_window(self):
        """保存当前活动窗口"""
        self._original_window = WindowHelper.get_current_window()
        return self._original_window
    
    def set_target_window(self, hwnd):
        """设置目标窗口"""
        self._target_window = hwnd
    
    def activate_target(self):
        """激活目标窗口"""
        if not self._target_window:
            # 如果没有指定目标窗口，自动获取前一个窗口
            self._target_window = WindowHelper.get_previous_window(
                exclude_hwnds=[self._original_window] if self._original_window else []
            )
        
        if self._target_window and win32gui.IsWindow(self._target_window):
            # 附加线程输入
            self._attached_threads = WindowHelper.attach_thread_input(self._target_window)
            # 激活窗口
            return WindowHelper.set_foreground_window(self._target_window)
        return False
    
    def restore_original(self):
        """恢复原始窗口"""
        # 分离线程输入
        if self._attached_threads:
            WindowHelper.detach_thread_input(self._attached_threads)
            self._attached_threads = None
        
        # 恢复原始窗口
        if self._original_window and win32gui.IsWindow(self._original_window):
            WindowHelper.set_foreground_window(self._original_window)
    
    def get_target_info(self):
        """获取目标窗口信息"""
        if self._target_window:
            return WindowHelper.get_window_info(self._target_window)
        return None
