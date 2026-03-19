"""
视频预览播放器
"""
import subprocess
import tempfile
import os
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QFileDialog
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor

try:
    from crop_selector import CropSelector
except ImportError:
    from video_to_gif.crop_selector import CropSelector


class VideoPlayer(QWidget):
    """视频预览播放器组件"""
    
    # 信号
    position_changed = pyqtSignal(float)  # 播放位置变化（秒）
    duration_changed = pyqtSignal(float)  # 视频时长变化（秒）
    crop_changed = pyqtSignal(QRect)  # 裁切区域变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 视频信息
        self.video_path = ""
        self.video_info = {}
        self.duration = 0.0
        self.position = 0.0
        self.video_size = (0, 0)
        
        # 临时文件
        self.temp_dir = None
        self.frame_files = []
        
        # 播放状态
        self.is_playing = False
        self.playback_speed = 1.0
        
        # 定时器
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self._update_playback)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 视频显示区域容器
        self.video_container = QWidget()
        self.video_container.setMinimumSize(400, 300)
        self.video_container.setStyleSheet("background-color: #1a1a1a;")
        
        # 视频显示标签
        self.video_label = QLabel(self.video_container)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("请选择视频文件")
        self.video_label.setStyleSheet("color: #888; font-size: 14px;")
        
        # 裁切选择器（叠加在视频上）
        self.crop_selector = CropSelector(self.video_container)
        self.crop_selector.crop_changed.connect(self._on_crop_changed)
        self.crop_selector.hide()
        
        layout.addWidget(self.video_container)
        
        # 控制栏
        control_layout = QHBoxLayout()
        
        # 播放/暂停按钮
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(30, 30)
        self.play_btn.clicked.connect(self._toggle_play)
        self.play_btn.setEnabled(False)
        control_layout.addWidget(self.play_btn)
        
        # 时间显示
        self.time_label = QLabel("00:00:00.000 / 00:00:00.000")
        control_layout.addWidget(self.time_label)
        
        control_layout.addStretch()
        
        # 重置裁切按钮
        self.reset_crop_btn = QPushButton("重置裁切")
        self.reset_crop_btn.clicked.connect(self._reset_crop)
        self.reset_crop_btn.setEnabled(False)
        control_layout.addWidget(self.reset_crop_btn)
        
        layout.addLayout(control_layout)
        
        # 进度滑块
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.setEnabled(False)
        layout.addWidget(self.progress_slider)
        
        # 布局调整时更新视频显示位置
        self.video_container.resizeEvent = self._on_container_resized
    
    def _on_container_resized(self, event):
        """容器大小变化时调整视频显示"""
        # 调用原始的resizeEvent
        QWidget.resizeEvent(self.video_container, event)
        self._update_video_display()
    
    def _update_video_display(self):
        """更新视频显示位置和大小"""
        if not self.video_size[0] or not self.video_size[1]:
            return
        
        container_w = self.video_container.width()
        container_h = self.video_container.height()
        
        # 计算缩放后的尺寸（保持宽高比）
        video_w, video_h = self.video_size
        scale = min(container_w / video_w, container_h / video_h)
        
        display_w = int(video_w * scale)
        display_h = int(video_h * scale)
        
        # 居中显示
        x = (container_w - display_w) // 2
        y = (container_h - display_h) // 2
        
        # 更新视频标签位置和大小
        self.video_label.setGeometry(x, y, display_w, display_h)
        
        # 更新裁切选择器
        self.crop_selector.set_display_rect(QRect(x, y, display_w, display_h))
    
    def load_video(self, video_path: str) -> bool:
        """加载视频文件"""
        try:
            # 先清理之前的视频资源
            self._cleanup_current_video()
            
            self.video_path = video_path
            
            # 获取视频信息
            self.video_info = self._get_video_info(video_path)
            self.duration = self.video_info.get('duration', 0)
            self.video_size = (self.video_info.get('width', 0), self.video_info.get('height', 0))
            
            if self.duration == 0 or self.video_size[0] == 0:
                return False
            
            # 创建临时目录
            self._create_temp_dir()
            
            # 提取关键帧
            self._extract_frames()
            
            # 设置裁切选择器
            self.crop_selector.set_video_size(self.video_size[0], self.video_size[1])
            self.crop_selector.show()
            
            # 更新UI
            self.duration_changed.emit(self.duration)
            self._update_time_label()
            self.progress_slider.setEnabled(True)
            self.play_btn.setEnabled(True)
            self.reset_crop_btn.setEnabled(True)
            self.video_label.setText("")
            
            # 更新视频显示位置（必须在显示第一帧之前）
            self._update_video_display()
            
            # 强制刷新布局
            self.video_container.updateGeometry()
            self.video_container.adjustSize()
            
            # 显示第一帧
            self._show_frame_at(0)
            
            return True
            
        except Exception as e:
            print(f"加载视频失败: {e}")
            return False
    
    def _cleanup_current_video(self):
        """清理当前视频资源"""
        # 停止播放
        self._pause()
        
        # 清理临时文件
        self._cleanup_temp()
        
        # 重置状态
        self.position = 0.0
        self.progress_slider.setValue(0)
        self.video_label.clear()
        self.video_label.setText("请选择视频文件")
        
        # 重置裁切选择器
        self.crop_selector.hide()
        self.crop_selector.set_video_size(0, 0)
    
    def _get_video_info(self, video_path: str) -> dict:
        """获取视频信息"""
        try:
            # 使用ffprobe获取视频信息
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,duration,r_frame_rate',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ]
            
            # Windows上处理中文路径，使用正确的编码
            result = subprocess.run(cmd, capture_output=True)
            import json
            # 尝试用gbk解码
            try:
                stdout = result.stdout.decode('gbk', errors='ignore')
            except:
                stdout = result.stdout.decode('utf-8', errors='ignore')
            data = json.loads(stdout)
            
            info = {}
            
            # 从stream获取信息
            if 'streams' in data and len(data['streams']) > 0:
                stream = data['streams'][0]
                info['width'] = int(stream.get('width', 0))
                info['height'] = int(stream.get('height', 0))
                
                # 解析帧率
                fps_str = stream.get('r_frame_rate', '0/1')
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    info['fps'] = float(num) / float(den) if float(den) != 0 else 0
                else:
                    info['fps'] = float(fps_str)
            
            # 获取时长
            duration = 0
            if 'format' in data and 'duration' in data['format']:
                duration = float(data['format']['duration'])
            elif 'streams' in data and len(data['streams']) > 0 and 'duration' in data['streams'][0]:
                duration = float(data['streams'][0]['duration'])
            
            info['duration'] = duration
            
            return info
            
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return {'width': 0, 'height': 0, 'duration': 0, 'fps': 0}
    
    def _create_temp_dir(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp(prefix="video_to_gif_")
    
    def _cleanup_temp(self):
        """清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
        self.frame_files = []
    
    def _extract_frames(self):
        """提取视频关键帧用于预览"""
        if not self.temp_dir:
            return
        
        # 提取更多关键帧以提高播放流畅度
        num_frames = 120
        interval = self.duration / num_frames if self.duration > 0 else 1
        
        for i in range(num_frames + 1):
            time_pos = i * interval
            frame_path = os.path.join(self.temp_dir, f"frame_{i:04d}.jpg")
            
            # 使用更快的提取参数
            cmd = [
                'ffmpeg',
                '-ss', str(time_pos),
                '-i', self.video_path,
                '-vframes', '1',
                '-q:v', '5',  # 降低质量以提高速度
                '-vf', 'scale=480:-1',  # 限制预览图尺寸
                '-y',
                frame_path
            ]
            
            try:
                # Windows上处理中文路径，使用正确的编码
                subprocess.run(cmd, capture_output=True, timeout=10)
                if os.path.exists(frame_path):
                    self.frame_files.append((time_pos, frame_path))
            except Exception as e:
                print(f"提取帧失败: {e}")
        
        # 按时间排序
        self.frame_files.sort(key=lambda x: x[0])
    
    def _show_frame_at(self, time_pos: float):
        """显示指定时间的帧"""
        # 找到最接近的帧
        closest_frame = None
        min_diff = float('inf')
        
        for frame_time, frame_path in self.frame_files:
            diff = abs(frame_time - time_pos)
            if diff < min_diff:
                min_diff = diff
                closest_frame = frame_path
        
        if closest_frame and os.path.exists(closest_frame):
            pixmap = QPixmap(closest_frame)
            if not pixmap.isNull():
                # 获取视频显示区域的实际尺寸
                display_rect = self.video_label.geometry()
                display_w = display_rect.width()
                display_h = display_rect.height()
                
                # 如果尺寸为0，使用容器尺寸计算
                if display_w <= 0 or display_h <= 0:
                    self._update_video_display()
                    display_rect = self.video_label.geometry()
                    display_w = display_rect.width()
                    display_h = display_rect.height()
                
                # 缩放以适应显示区域
                if display_w > 0 and display_h > 0:
                    scaled_pixmap = pixmap.scaled(
                        display_w,
                        display_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.video_label.setPixmap(scaled_pixmap)
    
    def _toggle_play(self):
        """切换播放/暂停"""
        if self.is_playing:
            self._pause()
        else:
            self._play()
    
    def _play(self):
        """开始播放"""
        self.is_playing = True
        self.play_btn.setText("⏸")
        self.playback_timer.start(33)  # 33ms更新一次，约30fps更流畅
    
    def _pause(self):
        """暂停播放"""
        self.is_playing = False
        self.play_btn.setText("▶")
        self.playback_timer.stop()
    
    def _update_playback(self):
        """更新播放进度"""
        if not self.is_playing:
            return
        
        # 更新位置（33ms更新一次，每次前进0.033秒，相当于1倍速）
        self.position += 0.033 * self.playback_speed
        
        if self.position >= self.duration:
            self.position = 0
        
        # 更新UI
        self.progress_slider.setValue(int(self.position / self.duration * 1000))
        self._update_time_label()
        self._show_frame_at(self.position)
        self.position_changed.emit(self.position)
    
    def _on_slider_moved(self, value):
        """滑块被拖动"""
        self.position = value / 1000 * self.duration
        self._update_time_label()
        self._show_frame_at(self.position)
        self.position_changed.emit(self.position)
    
    def _on_slider_pressed(self):
        """滑块被按下"""
        self._pause()
    
    def _on_slider_released(self):
        """滑块被释放"""
        pass
    
    def _update_time_label(self):
        """更新时间标签"""
        current = self._format_time(self.position)
        total = self._format_time(self.duration)
        self.time_label.setText(f"{current} / {total}")
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间为 HH:MM:SS.mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _on_crop_changed(self, rect):
        """裁切区域变化"""
        self.crop_changed.emit(rect)
    
    def _reset_crop(self):
        """重置裁切区域"""
        self.crop_selector.reset_crop()
    
    def get_crop_rect(self) -> QRect:
        """获取裁切区域"""
        return self.crop_selector.get_crop_rect()
    
    def set_crop_rect(self, rect: QRect):
        """设置裁切区域"""
        self.crop_selector.set_crop_rect(rect)
    
    def get_duration(self) -> float:
        """获取视频时长"""
        return self.duration
    
    def get_position(self) -> float:
        """获取当前位置"""
        return self.position
    
    def get_video_size(self) -> tuple:
        """获取视频尺寸"""
        return self.video_size
    
    def cleanup(self):
        """清理资源"""
        self._pause()
        self._cleanup_temp()
