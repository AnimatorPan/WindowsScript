"""
文件监控器 - 监控指定目录的文件变化
"""
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import threading
import queue

logger = logging.getLogger(__name__)


class FileChangeHandler(FileSystemEventHandler):
    """文件变化事件处理器"""
    
    def __init__(self, callback_queue):
        super().__init__()
        self.callback_queue = callback_queue
    
    def on_created(self, event):
        """文件创建"""
        if not event.is_directory:
            logger.info(f"文件创建: {event.src_path}")
            self.callback_queue.put(('created', str(event.src_path)))
    
    def on_modified(self, event):
        """文件修改"""
        if not event.is_directory:
            logger.info(f"文件修改: {event.src_path}")
            self.callback_queue.put(('modified', str(event.src_path)))
    
    def on_deleted(self, event):
        """文件删除"""
        if not event.is_directory:
            logger.info(f"文件删除: {event.src_path}")
            self.callback_queue.put(('deleted', str(event.src_path)))
    
    def on_moved(self, event):
        """文件移动"""
        if not event.is_directory:
            logger.info(f"文件移动: {event.src_path} -> {event.dest_path}")
            self.callback_queue.put(('moved', str(event.dest_path)))


class FileWatcher:
    """文件监控器"""
    
    def __init__(self, watch_path, callback=None):
        """
        初始化监控器
        
        Args:
            watch_path: 要监控的目录路径
            callback: 文件变化回调函数 (event_type, path)
        """
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.observer = None
        self.event_queue = queue.Queue()
        self.running = False
    
    def start(self):
        """启动监控"""
        if self.running:
            logger.warning("监控已在运行")
            return
        
        self.running = True
        
        event_handler = FileChangeHandler(self.event_queue)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_path), recursive=True)
        
        def process_events():
            while self.running:
                try:
                    event_type, path = self.event_queue.get(timeout=1)
                    if event_type and path:
                        if self.callback:
                            self.callback(event_type, path)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"处理事件失败: {e}")
        
        self.observer.start()
        self.process_thread = threading.Thread(target=process_events, daemon=True)
        self.process_thread.start()
        
        logger.info(f"开始监控: {self.watch_path}")
    
    def stop(self):
        """停止监控"""
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        logger.info(f"停止监控: {self.watch_path}")
    
    def is_running(self):
        """检查是否在运行"""
        return self.running
