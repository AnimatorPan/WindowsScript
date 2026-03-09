import json
import os


class Preset:
    """预设动作组合"""
    
    def __init__(self, name, actions, description=""):
        self.name = name
        self.actions = actions  # 动作列表
        self.description = description
    
    def to_dict(self):
        return {
            'name': self.name,
            'actions': self.actions,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get('name', '未命名'),
            actions=data.get('actions', []),
            description=data.get('description', '')
        )


class PresetManager:
    """预设管理器"""
    
    DEFAULT_PRESETS = [
        {
            'name': 'spine序列k帧',
            'description': 'Spine动画序列K帧：R(旋转模式) -> Ctrl+Shift+Right(下一关键帧) -> H(设置关键帧)',
            'actions': [
                {'type': 'key_press', 'params': {'key': 'r'}},
                {'type': 'key_press', 'params': {'key': 'right', 'modifiers': ['ctrl', 'shift']}},
                {'type': 'key_press', 'params': {'key': 'h'}},
            ]
        },
        {
            'name': '复制粘贴',
            'description': 'Ctrl+C, Ctrl+V',
            'actions': [
                {'type': 'key_press', 'params': {'key': 'c', 'modifiers': ['ctrl']}},
                {'type': 'delay', 'params': {'ms': 100}},
                {'type': 'key_press', 'params': {'key': 'v', 'modifiers': ['ctrl']}},
            ]
        },
    ]
    
    def __init__(self, preset_file=None):
        if preset_file is None:
            # 默认保存到用户目录
            app_dir = os.path.join(os.path.expanduser('~'), '.key_automation')
            os.makedirs(app_dir, exist_ok=True)
            self.preset_file = os.path.join(app_dir, 'presets.json')
        else:
            self.preset_file = preset_file
        
        self.presets = []
        self._load_presets()
    
    def _load_presets(self):
        """加载预设"""
        if os.path.exists(self.preset_file):
            try:
                with open(self.preset_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.presets = [Preset.from_dict(p) for p in data.get('presets', [])]
            except Exception:
                self.presets = []
        
        # 如果没有预设，添加默认预设
        if not self.presets:
            self.presets = [Preset.from_dict(p) for p in self.DEFAULT_PRESETS]
            self._save_presets()
    
    def _save_presets(self):
        """保存预设到文件"""
        try:
            data = {
                'presets': [p.to_dict() for p in self.presets]
            }
            with open(self.preset_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def get_all_presets(self):
        """获取所有预设"""
        return self.presets
    
    def get_preset(self, index):
        """获取指定预设"""
        if 0 <= index < len(self.presets):
            return self.presets[index]
        return None
    
    def add_preset(self, name, actions, description=""):
        """添加预设"""
        preset = Preset(name, actions, description)
        self.presets.append(preset)
        self._save_presets()
        return len(self.presets) - 1
    
    def update_preset(self, index, name=None, actions=None, description=None):
        """更新预设"""
        if 0 <= index < len(self.presets):
            preset = self.presets[index]
            if name is not None:
                preset.name = name
            if actions is not None:
                preset.actions = actions
            if description is not None:
                preset.description = description
            self._save_presets()
            return True
        return False
    
    def remove_preset(self, index):
        """删除预设"""
        if 0 <= index < len(self.presets):
            self.presets.pop(index)
            self._save_presets()
            return True
        return False
    
    def move_preset_up(self, index):
        """上移预设"""
        if index > 0 and index < len(self.presets):
            self.presets[index], self.presets[index - 1] = \
                self.presets[index - 1], self.presets[index]
            self._save_presets()
            return index - 1
        return index
    
    def move_preset_down(self, index):
        """下移预设"""
        if index >= 0 and index < len(self.presets) - 1:
            self.presets[index], self.presets[index + 1] = \
                self.presets[index + 1], self.presets[index]
            self._save_presets()
            return index + 1
        return index
    
    def import_preset(self, file_path):
        """从文件导入预设"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 支持单条预设或预设列表
            if 'presets' in data:
                for p in data['presets']:
                    self.presets.append(Preset.from_dict(p))
            else:
                self.presets.append(Preset.from_dict(data))
            
            self._save_presets()
            return True
        except Exception:
            return False
    
    def export_preset(self, index, file_path):
        """导出预设到文件"""
        if 0 <= index < len(self.presets):
            try:
                preset = self.presets[index]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(preset.to_dict(), f, ensure_ascii=False, indent=2)
                return True
            except Exception:
                return False
        return False
    
    def reset_to_default(self):
        """重置为默认预设"""
        self.presets = [Preset.from_dict(p) for p in self.DEFAULT_PRESETS]
        self._save_presets()
