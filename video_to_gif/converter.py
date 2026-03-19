"""
GIF转换核心逻辑
"""
import subprocess
import os
import re
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """转换结果"""
    success: bool
    output_path: str
    file_size: int
    duration: float
    error_message: str = ""


@dataclass
class ConversionConfig:
    """转换配置"""
    video_path: str
    output_path: str
    start_time: float
    end_time: float
    crop_x: int
    crop_y: int
    crop_w: int
    crop_h: int
    output_scale: int  # 输出缩放比例，如100表示100%
    fps: int
    color_quality: int  # 256, 128, 64, 32
    optimization_level: str  # 'high', 'standard', 'compressed', 'extreme'


class GIFConverterThread(QThread):
    """GIF转换后台线程"""
    
    # 信号
    progress_changed = pyqtSignal(int, str)  # 进度(0-100), 状态信息
    conversion_finished = pyqtSignal(ConversionResult)
    
    def __init__(self, config: ConversionConfig):
        super().__init__()
        self.config = config
        self.is_cancelled = False
        self.ffmpeg_path = self._get_ffmpeg_path()
    
    def _get_ffmpeg_path(self) -> str:
        """获取FFmpeg可执行文件路径"""
        # 首先检查内置的FFmpeg
        script_dir = Path(__file__).parent
        builtin_ffmpeg = script_dir / "ffmpeg" / "ffmpeg.exe"
        
        if builtin_ffmpeg.exists():
            return str(builtin_ffmpeg)
        
        # 检查系统PATH中的FFmpeg
        try:
            result = subprocess.run(['where', 'ffmpeg'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return 'ffmpeg'
        except:
            pass
        
        return 'ffmpeg'
    
    def cancel(self):
        """取消转换"""
        self.is_cancelled = True
        self.terminate()
    
    def run(self):
        """执行转换"""
        try:
            result = self._convert()
            self.conversion_finished.emit(result)
        except Exception as e:
            result = ConversionResult(
                success=False,
                output_path="",
                file_size=0,
                duration=0,
                error_message=str(e)
            )
            self.conversion_finished.emit(result)
    
    def _convert(self) -> ConversionResult:
        """执行GIF转换"""
        cfg = self.config
        
        # 计算时长
        duration = cfg.end_time - cfg.start_time
        if duration <= 0:
            return ConversionResult(
                success=False,
                output_path="",
                file_size=0,
                duration=0,
                error_message="时间范围无效"
            )
        
        # 构建视频滤镜
        filters = []
        
        # 1. 设置帧率
        filters.append(f"fps={cfg.fps}")
        
        # 2. 裁切
        if cfg.crop_w > 0 and cfg.crop_h > 0:
            filters.append(f"crop={cfg.crop_w}:{cfg.crop_h}:{cfg.crop_x}:{cfg.crop_y}")
        
        # 3. 缩放 - 根据输出比例计算实际尺寸
        if cfg.output_scale != 100:
            # 使用百分比缩放
            scale_factor = cfg.output_scale / 100.0
            filters.append(f"scale=iw*{scale_factor}:ih*{scale_factor}:flags=lanczos")
        # 如果比例为100%，保持原始裁切后的尺寸，不添加缩放滤镜
        
        # 4. 调色板优化
        color_count = cfg.color_quality
        
        # 根据优化级别调整参数
        if cfg.optimization_level == 'high':
            palettegen_opts = f"max_colors={color_count}"
            paletteuse_opts = ""
        elif cfg.optimization_level == 'standard':
            palettegen_opts = f"max_colors={color_count}"
            paletteuse_opts = "dither=bayer"
        elif cfg.optimization_level == 'compressed':
            palettegen_opts = f"max_colors={color_count}"
            paletteuse_opts = "dither=bayer"
        else:  # extreme
            palettegen_opts = f"max_colors={color_count}"
            paletteuse_opts = "dither=bayer"
        
        filters.append(f"split[s0][s1];[s0]palettegen={palettegen_opts}[p];[s1][p]paletteuse={paletteuse_opts}")
        
        vf = ",".join(filters)
        
        # 构建FFmpeg命令
        cmd = [
            self.ffmpeg_path,
            '-ss', str(cfg.start_time),
            '-t', str(duration),
            '-i', cfg.video_path,
            '-vf', vf,
            '-loop', '0',
            '-y',
            cfg.output_path
        ]
        
        # 执行转换
        self.progress_changed.emit(0, "开始转换...")
        
        try:
            # Windows上处理中文路径，使用正确的编码
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 解析进度
            error_output_bytes = []
            while True:
                if self.is_cancelled:
                    process.terminate()
                    return ConversionResult(
                        success=False,
                        output_path="",
                        file_size=0,
                        duration=0,
                        error_message="用户取消"
                    )
                
                line_bytes = process.stderr.readline()
                if not line_bytes:
                    break
                
                # 保存错误输出用于调试
                error_output_bytes.append(line_bytes)
                
                # 尝试用gbk解码
                try:
                    line = line_bytes.decode('gbk', errors='ignore')
                except:
                    line = line_bytes.decode('utf-8', errors='ignore')
                
                # 解析进度
                progress = self._parse_progress(line, duration)
                if progress > 0:
                    self.progress_changed.emit(progress, f"转换中... {progress}%")
            
            process.wait()
            
            # 先检查输出文件是否存在
            if os.path.exists(cfg.output_path):
                # 输出文件存在，认为成功
                pass
            elif process.returncode != 0:
                # 输出文件不存在，且返回码非0，才认为是错误
                try:
                    error_output = b''.join(error_output_bytes).decode('gbk', errors='ignore')
                except:
                    error_output = b''.join(error_output_bytes).decode('utf-8', errors='ignore')
                return ConversionResult(
                    success=False,
                    output_path="",
                    file_size=0,
                    duration=0,
                    error_message=f"FFmpeg错误: {error_output[:200]}"
                )
            else:
                return ConversionResult(
                    success=False,
                    output_path="",
                    file_size=0,
                    duration=0,
                    error_message="输出文件未生成"
                )
            
            file_size = os.path.getsize(cfg.output_path)
            
            self.progress_changed.emit(100, "转换完成")
            
            return ConversionResult(
                success=True,
                output_path=cfg.output_path,
                file_size=file_size,
                duration=duration
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                output_path="",
                file_size=0,
                duration=0,
                error_message=f"转换异常: {str(e)}"
            )
    
    def _parse_progress(self, line: str, total_duration: float) -> int:
        """解析FFmpeg输出中的进度信息"""
        # 查找时间信息
        match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            current_time = hours * 3600 + minutes * 60 + seconds
            
            if total_duration > 0:
                progress = int((current_time / total_duration) * 100)
                return min(99, max(0, progress))
        
        return 0


class GIFConverter:
    """GIF转换器"""
    
    def __init__(self):
        self.current_thread = None
    
    def convert(self, config: ConversionConfig, 
                progress_callback=None, 
                finished_callback=None) -> GIFConverterThread:
        """开始转换"""
        # 停止之前的转换
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.cancel()
            self.current_thread.wait()
        
        # 创建新线程
        self.current_thread = GIFConverterThread(config)
        
        if progress_callback:
            self.current_thread.progress_changed.connect(progress_callback)
        
        if finished_callback:
            self.current_thread.conversion_finished.connect(finished_callback)
        
        self.current_thread.start()
        return self.current_thread
    
    def cancel(self):
        """取消当前转换"""
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.cancel()
    
    def estimate_file_size(self, config: ConversionConfig) -> int:
        """预估文件大小（字节）"""
        # 简单的估算公式
        duration = config.end_time - config.start_time
        frame_count = int(duration * config.fps)
        
        # 每帧大致大小（根据颜色质量和尺寸）
        # 根据缩放比例计算实际输出尺寸
        scale_factor = config.output_scale / 100.0
        
        # 如果裁切区域为0，使用默认尺寸（640x480）
        if config.crop_w > 0 and config.crop_h > 0:
            output_w = int(config.crop_w * scale_factor)
            output_h = int(config.crop_h * scale_factor)
        else:
            # 默认尺寸
            output_w = int(640 * scale_factor)
            output_h = int(480 * scale_factor)
        
        pixel_count = output_w * output_h
        
        # 根据优化级别调整（根据实际测试结果调整）
        # 实际文件比预估大约1.7倍，相应调整压缩率
        compression_ratio = {
            'high': 0.85,      # 高质量压缩率低，文件大
            'standard': 0.36,
            'compressed': 0.3,
            'extreme': 0.2,
        }.get(config.optimization_level, 0.7)
        
        # 根据颜色数量调整
        color_ratio = config.color_quality / 256
        
        # 预估公式：帧数 × 像素数 × 压缩率 × 颜色比例
        # 根据实际测试调整系数，使预估更接近实际
        estimated_size = int(frame_count * pixel_count * compression_ratio * color_ratio * 0.30)
        
        return max(1024, estimated_size)  # 至少1KB
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
