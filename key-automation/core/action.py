class Action:
    """按键动作基类"""
    TYPE_KEY_PRESS = "key_press"
    TYPE_KEY_DOWN = "key_down"
    TYPE_KEY_UP = "key_up"
    TYPE_MOUSE_CLICK = "mouse_click"
    TYPE_MOUSE_MOVE = "mouse_move"
    TYPE_DELAY = "delay"
    
    ACTION_TYPES = {
        TYPE_KEY_PRESS: "按键",
        TYPE_KEY_DOWN: "按下",
        TYPE_KEY_UP: "释放",
        TYPE_MOUSE_CLICK: "鼠标点击",
        TYPE_MOUSE_MOVE: "鼠标移动",
        TYPE_DELAY: "延迟"
    }
    
    def __init__(self, action_type, params=None):
        self.type = action_type
        self.params = params or {}
    
    def __str__(self):
        type_name = self.ACTION_TYPES.get(self.type, self.type)
        
        if self.type == self.TYPE_KEY_PRESS:
            key = self.params.get('key', '')
            modifiers = self.params.get('modifiers', [])
            if modifiers:
                mod_str = '+'.join(modifiers)
                return f"按键: {mod_str}+{key}"
            return f"按键: {key}"
        elif self.type == self.TYPE_KEY_DOWN:
            key = self.params.get('key', '')
            modifiers = self.params.get('modifiers', [])
            if modifiers:
                mod_str = '+'.join(modifiers)
                return f"按下: {mod_str}+{key}"
            return f"按下: {key}"
        elif self.type == self.TYPE_KEY_UP:
            key = self.params.get('key', '')
            modifiers = self.params.get('modifiers', [])
            if modifiers:
                mod_str = '+'.join(modifiers)
                return f"释放: {mod_str}+{key}"
            return f"释放: {key}"
        elif self.type == self.TYPE_MOUSE_CLICK:
            button = self.params.get('button', 'left')
            x = self.params.get('x')
            y = self.params.get('y')
            if x is not None and y is not None:
                return f"鼠标点击 [{button}]: ({x}, {y})"
            return f"鼠标点击 [{button}]"
        elif self.type == self.TYPE_MOUSE_MOVE:
            x = self.params.get('x', 0)
            y = self.params.get('y', 0)
            return f"鼠标移动: ({x}, {y})"
        elif self.type == self.TYPE_DELAY:
            ms = self.params.get('ms', 0)
            return f"延迟: {ms}ms"
        
        return f"{type_name}: {self.params}"
    
    def to_dict(self):
        return {
            'type': self.type,
            'params': self.params
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['type'], data['params'])


class ActionList:
    """管理动作列表"""
    
    def __init__(self):
        self.actions = []
    
    def add_action(self, action, index=None):
        """添加动作，如果指定index则插入到该位置"""
        if index is None:
            self.actions.append(action)
        else:
            self.actions.insert(index, action)
        return len(self.actions) - 1
    
    def remove_action(self, index):
        """删除指定索引的动作"""
        if 0 <= index < len(self.actions):
            return self.actions.pop(index)
        return None
    
    def move_up(self, index):
        """将动作上移一位"""
        if index > 0 and index < len(self.actions):
            self.actions[index], self.actions[index - 1] = \
                self.actions[index - 1], self.actions[index]
            return index - 1
        return index
    
    def move_down(self, index):
        """将动作下移一位"""
        if index >= 0 and index < len(self.actions) - 1:
            self.actions[index], self.actions[index + 1] = \
                self.actions[index + 1], self.actions[index]
            return index + 1
        return index
    
    def clear(self):
        """清空所有动作"""
        self.actions.clear()
    
    def get_action(self, index):
        """获取指定索引的动作"""
        if 0 <= index < len(self.actions):
            return self.actions[index]
        return None
    
    def __len__(self):
        return len(self.actions)
    
    def __iter__(self):
        return iter(self.actions)
    
    def to_list(self):
        """转换为列表"""
        return [action.to_dict() for action in self.actions]
    
    def from_list(self, data_list):
        """从列表加载"""
        self.actions = [Action.from_dict(data) for data in data_list]
