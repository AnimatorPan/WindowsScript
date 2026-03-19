"""
配置文件管理模块
用于保存和加载程序设置，包括文件路径
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AppConfig:
    """应用程序配置数据类"""
    source_path: str = ""
    target_path: str = ""
    ignore_image_formats: bool = False
    compare_content: bool = True
    window_width: int = 900
    window_height: int = 700


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        # 配置文件路径：放在用户目录下的 .file_copier 文件夹中
        self.config_dir = Path.home() / ".file_copier"
        self.config_file = self.config_dir / "config.json"
        self._config = AppConfig()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> AppConfig:
        """
        从文件加载配置
        
        Returns:
            AppConfig: 加载的配置对象
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = AppConfig(**data)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # 配置文件损坏或格式错误，使用默认配置
            print(f"配置文件加载失败，使用默认配置: {e}")
            self._config = AppConfig()
        
        return self._config
    
    def save(self, config: Optional[AppConfig] = None):
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置对象，为 None 则保存当前配置
        """
        if config is not None:
            self._config = config
        
        try:
            self._ensure_config_dir()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._config), f, ensure_ascii=False, indent=2)
        except (OSError, IOError) as e:
            print(f"配置文件保存失败: {e}")
    
    def get_config(self) -> AppConfig:
        """获取当前配置"""
        return self._config
    
    def update_paths(self, source_path: str = "", target_path: str = ""):
        """
        更新路径配置
        
        Args:
            source_path: 源文件夹路径
            target_path: 目标文件夹路径
        """
        if source_path:
            self._config.source_path = source_path
        if target_path:
            self._config.target_path = target_path
    
    def update_settings(self, ignore_image_formats: Optional[bool] = None, 
                       compare_content: Optional[bool] = None):
        """
        更新设置
        
        Args:
            ignore_image_formats: 是否忽略图片格式
            compare_content: 是否比较文件内容
        """
        if ignore_image_formats is not None:
            self._config.ignore_image_formats = ignore_image_formats
        if compare_content is not None:
            self._config.compare_content = compare_content
    
    def update_window_size(self, width: int, height: int):
        """
        更新窗口大小
        
        Args:
            width: 窗口宽度
            height: 窗口高度
        """
        self._config.window_width = width
        self._config.window_height = height


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例（单例模式）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
