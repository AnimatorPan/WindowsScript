"""
视频预览播放器 - 极致性能优化版 v4 (预加载关键帧方案)

播放慢的原因：实时解码每帧需要100-300ms，无法达到30fps
解决方案：预加载所有关键帧到内存，播放时直接读取
"""
import subprocess
import tempfile
import os
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QFileDialog
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QThread, QObject
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
from collections import OrderedDict

try:
    from crop_selector import CropSelector
except ImportError:
    from video_to_gif.crop_selector import CropSelector


class VideoLoadWorker(QObject):
    """视频加载工作线程 - 预加载关键帧"""
    
    first_frame_ready = pyqtSignal(str)  # 首帧路径
    keyframe_loaded = pyqtSignal(int, int)  # 当前帧数, 总帧数
    all_keyframes_ready = pyqtSignal(dict, dict)  # 帧数据 {time: path}, 视频信息
    error_occurred = pyqtSignal(str)
    
    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = video_path
        self.is_cancelled = False
        self.temp_dir = None
        
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        """执行加载 - 预加载关键帧"""
        try:
            overall_start = time.time()
            
            # 1. 快速获取视频信息
            t0 = time.time()
            video_info = self._get_video_info_fast()
            print(f"[性能] 获取视频信息: {(time.time()-t0)*1000:.0f}ms")
            
            if self.is_cancelled:
                return
            
            duration = video_info.get('duration', 0)
            if duration == 0:
                self.error_occurred.emit("无法获取视频时长")
                return
            
            # 2. 创建临时目录
            self.temp_dir = tempfile.mkdtemp(prefix="video_to_gif_")
            
            # 3. 快速提取首帧
            t0 = time.time()
            first_frame = self._extract_first_frame_fast()
            print(f"[性能] 提取首帧: {(time.time()-t0)*1000:.0f}ms")
            
            if first_frame and not self.is_cancelled:
                self.first_frame_ready.emit(first_frame)
            
            # 4. 生成关键帧时间点（60帧均匀分布）
            num_frames = 60
            keyframe_times = [i * duration / num_frames for i in range(num_frames + 1)]
            
            # 5. 并行提取所有关键帧
            t0 = time.time()
            keyframe_frames = self._extract_keyframes_parallel(keyframe_times)
            print(f"[性能] 提取 {len(keyframe_frames)} 关键帧: {(time.time()-t0)*1000:.0f}ms")
            
            video_info['duration'] = duration
            video_info['num_frames'] = len(keyframe_frames)
            video_info['temp_dir'] = self.temp_dir
            
            self.all_keyframes_ready.emit(keyframe_frames, video_info)
            
            print(f"[性能] 总加载时间: {(time.time()-overall_start)*1000:.0f}ms")
                
        except Exception as e:
            print(f"[错误] 加载失败: {e}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))
    
    def _get_video_info_fast(self) -> dict:
        """快速获取视频信息"""
        info = {'width': 0, 'height': 0, 'duration': 0, 'fps': 30}
        
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,r_frame_rate',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1',
                self.video_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            stdout = result.stdout.decode('utf-8', errors='ignore')
            
            for line in stdout.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'width':
                        info['width'] = int(value) if value.isdigit() else 0
                    elif key == 'height':
                        info['height'] = int(value) if value.isdigit() else 0
                    elif key == 'duration':
                        try:
                            info['duration'] = float(value)
                        except:
                            pass
                    elif key == 'r_frame_rate':
                        try:
                            if '/' in value:
                                num, den = value.split('/')
                                info['fps'] = float(num) / float(den) if float(den) != 0 else 30
                            else:
                                info['fps'] = float(value)
                        except:
                            pass
            
            return info
            
        except Exception as e:
            print(f"[警告] 获取视频信息失败: {e}")
            return info
    
    def _extract_first_frame_fast(self) -> str:
        """快速提取首帧"""
        try:
            frame_path = os.path.join(self.temp_dir, "first_frame.jpg")
            
            cmd = [
                'ffmpeg',
                '-ss', '0',
                '-i', self.video_path,
                '-vframes', '1',
                '-q:v', '5',
                '-vf', 'scale=480:-1:flags=fast_bilinear',
                '-pix_fmt', 'yuvj420p',
                '-y',
                frame_path
            ]
            
            subprocess.run(
                cmd, 
                capture_output=True, 
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                return frame_path
            return None
            
        except Exception as e:
            print(f"[警告] 提取首帧失败: {e}")
            return None
    
    def _extract_keyframes_parallel(self, time_positions: list) -> dict:
        """并行提取关键帧"""
        frames = {}
        total = len(time_positions)
        completed = 0
        
        def extract_single(time_pos):
            nonlocal completed
            if self.is_cancelled:
                return None
            
            frame_path = os.path.join(self.temp_dir, f"kf_{completed:04d}.jpg")
            
            try:
                cmd = [
                    'ffmpeg',
                    '-ss', str(time_pos),
                    '-i', self.video_path,
                    '-vframes', '1',
                    '-q:v', '6',
                    '-vf', 'scale=480:-1:flags=fast_bilinear',
                    '-pix_fmt', 'yuvj420p',
                    '-y',
                    frame_path
                ]
                
                subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                    return time_pos, frame_path
                    
            except Exception as e:
                pass
            
            return None
        
        # 使用线程池并行提取 - 6个并发
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(extract_single, t): t for t in time_positions}
            
            for future in as_completed(futures):
                if self.is_cancelled:
                    break
                
                result = future.result()
                if result:
                    time_pos, path = result
                    frames[time_pos] = path
                
                completed += 1
                self.keyframe_loaded.emit(completed, total)
        
        return frames


class FrameCache:
    """LRU帧缓存"""
    
    def __init__(self, max_size: int = 30):
        self.max_size = max_size
        self.cache = OrderedDict()
        self._lock = threading.Lock()
    
    def get(self, key):
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def put(self, key, value):
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    self.cache.popitem(last=False)
                self.cache[key] = value
    
    def clear(self):
        with self._lock:
            self.cache.clear()


class VideoPlayer(QWidget):
    """视频预览播放器组件 - 预加载版"""
    
    position_changed = pyqtSignal(float)
    duration_changed = pyqtSignal(float)
    crop_changed = pyqtSignal(QRect)
    loading_progress = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.video_path = ""
        self.video_info = {}
        self.duration = 0.0
        self.position = 0.0
        self.video_size = (0, 0)
        self.keyframe_frames = {}  # 关键帧 {time: path}
        
        self.temp_dir = None
        
        self.is_playing = False
        self.playback_speed = 1.0
        self._is_loading = False
        self._keyframes_loaded = False
        
        self.frame_cache = FrameCache(max_size=30)
        
        self.load_thread = None
        self.load_worker = None
        
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self._update_playback)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.video_container = QWidget()
        self.video_container.setMinimumSize(400, 300)
        self.video_container.setStyleSheet("background-color: #1a1a1a;")
        
        self.video_label = QLabel(self.video_container)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("请选择视频文件")
        self.video_label.setStyleSheet("color: #888; font-size: 14px;")
        self.video_label.setGeometry(0, 0, 400, 300)
        
        self.crop_selector = CropSelector(self.video_container)
        self.crop_selector.crop_changed.connect(self._on_crop_changed)
        self.crop_selector.hide()
        
        self.loading_label = QLabel("", self.video_container)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            color: #4CAF50;
            font-size: 16px;
            font-weight: bold;
            background-color: rgba(0, 0, 0, 0.7);
            padding: 10px 20px;
            border-radius: 5px;
        """)
        self.loading_label.hide()
        
        layout.addWidget(self.video_container)
        
        control_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(30, 30)
        self.play_btn.clicked.connect(self._toggle_play)
        self.play_btn.setEnabled(False)
        control_layout.addWidget(self.play_btn)
        
        self.time_label = QLabel("00:00:00.000 / 00:00:00.000")
        control_layout.addWidget(self.time_label)
        
        control_layout.addStretch()
        
        self.reset_crop_btn = QPushButton("重置裁切")
        self.reset_crop_btn.clicked.connect(self._reset_crop)
        self.reset_crop_btn.setEnabled(False)
        control_layout.addWidget(self.reset_crop_btn)
        
        layout.addLayout(control_layout)
        
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.setEnabled(False)
        layout.addWidget(self.progress_slider)
        
        self.video_container.resizeEvent = self._on_container_resized
    
    def _on_container_resized(self, event):
        QWidget.resizeEvent(self.video_container, event)
        self._update_video_display()
        self._update_loading_label_position()
    
    def _update_loading_label_position(self):
        label_w = 200
        label_h = 40
        x = (self.video_container.width() - label_w) // 2
        y = (self.video_container.height() - label_h) // 2
        self.loading_label.setGeometry(x, y, label_w, label_h)
    
    def _update_video_display(self):
        if not self.video_size[0] or not self.video_size[1]:
            return
        
        container_w = self.video_container.width()
        container_h = self.video_container.height()
        
        if container_w <= 0:
            container_w = 400
        if container_h <= 0:
            container_h = 300
        
        video_w, video_h = self.video_size
        scale = min(container_w / video_w, container_h / video_h)
        
        display_w = int(video_w * scale)
        display_h = int(video_h * scale)
        
        x = (container_w - display_w) // 2
        y = (container_h - display_h) // 2
        
        self.video_label.setGeometry(x, y, display_w, display_h)
        self.crop_selector.set_display_rect(QRect(x, y, display_w, display_h))
    
    def load_video(self, video_path: str) -> bool:
        print(f"\n[加载] 开始加载视频: {video_path}")
        
        try:
            self._cancel_loading()
            self._cleanup_current_video()
            
            self.video_path = video_path
            self._is_loading = True
            self._keyframes_loaded = False
            
            self._show_loading("正在分析视频...")
            
            self.load_worker = VideoLoadWorker(video_path)
            self.load_worker.first_frame_ready.connect(self._on_first_frame_ready)
            self.load_worker.keyframe_loaded.connect(self._on_keyframe_loaded)
            self.load_worker.all_keyframes_ready.connect(self._on_all_keyframes_ready)
            self.load_worker.error_occurred.connect(self._on_load_error)
            
            self.load_thread = QThread()
            self.load_worker.moveToThread(self.load_thread)
            self.load_thread.started.connect(self.load_worker.run)
            self.load_thread.start()
            
            return True
            
        except Exception as e:
            print(f"[错误] 加载视频失败: {e}")
            self._hide_loading()
            self._is_loading = False
            return False
    
    def _cancel_loading(self):
        if self.load_worker:
            self.load_worker.cancel()
        if self.load_thread:
            self.load_thread.quit()
            self.load_thread.wait(1000)
    
    def _show_loading(self, text: str):
        self.loading_label.setText(text)
        self.loading_label.show()
        self._update_loading_label_position()
    
    def _hide_loading(self):
        self.loading_label.hide()
    
    def _on_first_frame_ready(self, frame_path: str):
        print(f"[加载] 首帧就绪，立即显示")
        self._update_video_display()
        self._show_frame(frame_path)
        self._show_loading("正在加载预览帧...")
    
    def _on_keyframe_loaded(self, current: int, total: int):
        self.loading_progress.emit(current, total)
        self._show_loading(f"加载预览帧... {current}/{total}")
    
    def _on_all_keyframes_ready(self, frames: dict, info: dict):
        print(f"[加载] 所有关键帧就绪: {len(frames)} 帧")
        
        self.keyframe_frames = frames
        self.video_info = info
        self.duration = info.get('duration', 0)
        self.video_size = (info.get('width', 0), info.get('height', 0))
        self.temp_dir = info.get('temp_dir')
        
        self._keyframes_loaded = True
        self._is_loading = False
        self._hide_loading()
        
        self.duration_changed.emit(self.duration)
        self._update_time_label()
        
        self.crop_selector.set_video_size(self.video_size[0], self.video_size[1])
        self.crop_selector.show()
        
        self.progress_slider.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.reset_crop_btn.setEnabled(True)
        self.video_label.setText("")
        
        self._update_video_display()
        self.video_container.updateGeometry()
        self.video_container.adjustSize()
        
        # 显示第一帧
        if self.keyframe_frames:
            first_time = min(self.keyframe_frames.keys())
            self._show_frame(self.keyframe_frames[first_time])
        
        print(f"[加载] 完成，可以播放")
    
    def _on_load_error(self, error: str):
        print(f"[错误] 加载错误: {error}")
        self._is_loading = False
        self._hide_loading()
        self._cleanup_current_video()
    
    def _cleanup_current_video(self):
        self._pause()
        self._cleanup_temp()
        self.frame_cache.clear()
        self.keyframe_frames.clear()
        
        self.position = 0.0
        self.progress_slider.setValue(0)
        self.video_label.clear()
        self.video_label.setText("请选择视频文件")
        
        self.crop_selector.hide()
        self.crop_selector.set_video_size(0, 0)
    
    def _cleanup_temp(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def _show_frame(self, frame_path: str):
        if not frame_path or not os.path.exists(frame_path):
            return
        
        cached_pixmap = self.frame_cache.get(frame_path)
        if cached_pixmap:
            self._display_pixmap(cached_pixmap)
            return
        
        pixmap = QPixmap(frame_path)
        if not pixmap.isNull():
            self.frame_cache.put(frame_path, pixmap)
            self._display_pixmap(pixmap)
    
    def _display_pixmap(self, pixmap: QPixmap):
        display_rect = self.video_label.geometry()
        display_w = display_rect.width()
        display_h = display_rect.height()
        
        if display_w <= 0 or display_h <= 0:
            self._update_video_display()
            display_rect = self.video_label.geometry()
            display_w = display_rect.width()
            display_h = display_rect.height()
        
        if display_w <= 0 or display_h <= 0:
            container_w = max(self.video_container.width(), 400)
            container_h = max(self.video_container.height(), 300)
            if self.video_size[0] > 0 and self.video_size[1] > 0:
                video_w, video_h = self.video_size
                scale = min(container_w / video_w, container_h / video_h)
                display_w = int(video_w * scale)
                display_h = int(video_h * scale)
            else:
                display_w = container_w
                display_h = container_h
        
        if display_w > 0 and display_h > 0:
            scaled_pixmap = pixmap.scaled(
                display_w,
                display_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)
    
    def _show_frame_at(self, time_pos: float):
        """显示指定时间的帧 - 从预加载的关键帧中查找"""
        if not self.keyframe_frames:
            return
        
        # 找到最接近的关键帧
        closest_time = None
        min_diff = float('inf')
        
        for t in self.keyframe_frames.keys():
            diff = abs(t - time_pos)
            if diff < min_diff:
                min_diff = diff
                closest_time = t
        
        if closest_time is not None:
            self._show_frame(self.keyframe_frames[closest_time])
    
    def _toggle_play(self):
        if self.is_playing:
            self._pause()
        else:
            self._play()
    
    def _play(self):
        if self._is_loading or not self._keyframes_loaded:
            return
        self.is_playing = True
        self.play_btn.setText("⏸")
        self.playback_timer.start(33)  # 30fps
    
    def _pause(self):
        self.is_playing = False
        self.play_btn.setText("▶")
        self.playback_timer.stop()
    
    def _update_playback(self):
        if not self.is_playing:
            return
        
        self.position += 0.033 * self.playback_speed
        
        if self.position >= self.duration:
            self.position = 0
        
        self.progress_slider.setValue(int(self.position / self.duration * 1000))
        self._update_time_label()
        self._show_frame_at(self.position)
        self.position_changed.emit(self.position)
    
    def _on_slider_moved(self, value):
        self.position = value / 1000 * self.duration
        self._update_time_label()
        self._show_frame_at(self.position)
        self.position_changed.emit(self.position)
    
    def _on_slider_pressed(self):
        self._pause()
    
    def _on_slider_released(self):
        pass
    
    def _update_time_label(self):
        current = self._format_time(self.position)
        total = self._format_time(self.duration)
        self.time_label.setText(f"{current} / {total}")
    
    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _on_crop_changed(self, rect):
        self.crop_changed.emit(rect)
    
    def _reset_crop(self):
        self.crop_selector.reset_crop()
    
    def get_crop_rect(self) -> QRect:
        return self.crop_selector.get_crop_rect()
    
    def set_crop_rect(self, rect: QRect):
        self.crop_selector.set_crop_rect(rect)
    
    def get_duration(self) -> float:
        return self.duration
    
    def get_position(self) -> float:
        return self.position
    
    def get_video_size(self) -> tuple:
        return self.video_size
    
    def is_loading(self) -> bool:
        return self._is_loading
    
    def cleanup(self):
        self._cancel_loading()
        self._pause()
        self._cleanup_temp()
        self.frame_cache.clear()
