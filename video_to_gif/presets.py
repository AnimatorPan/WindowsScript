"""
预设管理模块
"""
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class Preset:
    """预设配置"""
    name: str
    description: str
    fps: int
    color_quality: int
    optimization_level: str
    output_scale: int  # 输出缩放比例，如100表示100%


class PresetManager:
    """预设管理器"""
    
    # 默认预设
    DEFAULT_PRESETS = [
        Preset(
            name="高质量",
            description="色彩丰富，文件较大",
            fps=20,
            color_quality=256,
            optimization_level="high",
            output_scale=100
        ),
        Preset(
            name="标准",
            description="平衡质量和文件大小",
            fps=15,
            color_quality=128,
            optimization_level="standard",
            output_scale=75
        ),
        Preset(
            name="压缩优先",
            description="较小文件，适合分享",
            fps=10,
            color_quality=64,
            optimization_level="compressed",
            output_scale=50
        ),
        Preset(
            name="极致压缩",
            description="最小文件，适合简单动画",
            fps=8,
            color_quality=32,
            optimization_level="extreme",
            output_scale=30
        )
    ]
    
    def __init__(self):
        self.presets: List[Preset] = []
        self.config_file = self._get_config_path()
        self._load_presets()
    
    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        # 使用用户目录下的配置文件
        config_dir = Path.home() / ".video_to_gif"
        config_dir.mkdir(exist_ok=True)
        return config_dir / "presets.json"
    
    def _load_presets(self):
        """加载预设"""
        # 先添加默认预设
        self.presets = list(self.DEFAULT_PRESETS)
        
        # 加载用户自定义预设
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for item in data:
                    preset = Preset(**item)
                    # 检查是否已存在同名预设
                    if not any(p.name == preset.name for p in self.presets):
                        self.presets.append(preset)
                        
            except Exception as e:
                print(f"加载预设失败: {e}")
    
    def _save_presets(self):
        """保存预设到文件"""
        try:
            # 只保存非默认预设
            user_presets = [p for p in self.presets if p.name not in [dp.name for dp in self.DEFAULT_PRESETS]]
            data = [asdict(p) for p in user_presets]
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存预设失败: {e}")
    
    def get_all_presets(self) -> List[Preset]:
        """获取所有预设"""
        return list(self.presets)
    
    def get_preset(self, index: int) -> Optional[Preset]:
        """获取指定预设"""
        if 0 <= index < len(self.presets):
            return self.presets[index]
        return None
    
    def get_preset_by_name(self, name: str) -> Optional[Preset]:
        """通过名称获取预设"""
        for preset in self.presets:
            if preset.name == name:
                return preset
        return None
    
    def add_preset(self, preset: Preset) -> bool:
        """添加预设"""
        # 检查名称是否已存在
        if any(p.name == preset.name for p in self.presets):
            return False
        
        self.presets.append(preset)
        self._save_presets()
        return True
    
    def update_preset(self, index: int, preset: Preset) -> bool:
        """更新预设"""
        if 0 <= index < len(self.presets):
            # 检查是否是默认预设
            if self.presets[index].name in [dp.name for dp in self.DEFAULT_PRESETS]:
                # 默认预设不允许修改，创建新预设
                return self.add_preset(preset)
            
            self.presets[index] = preset
            self._save_presets()
            return True
        return False
    
    def remove_preset(self, index: int) -> bool:
        """删除预设"""
        if 0 <= index < len(self.presets):
            preset = self.presets[index]
            # 默认预设不允许删除
            if preset.name in [dp.name for dp in self.DEFAULT_PRESETS]:
                return False
            
            self.presets.pop(index)
            self._save_presets()
            return True
        return False
    
    def export_preset(self, index: int, file_path: str) -> bool:
        """导出预设"""
        preset = self.get_preset(index)
        if preset:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(preset), f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                print(f"导出预设失败: {e}")
        return False
    
    def import_preset(self, file_path: str) -> bool:
        """导入预设"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            preset = Preset(**data)
            return self.add_preset(preset)
            
        except Exception as e:
            print(f"导入预设失败: {e}")
            return False
