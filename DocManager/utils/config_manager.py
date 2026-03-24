"""
配置管理器 - 持久化应用设置和状态
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    _instance = None  # 单例

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.config_dir = Path.home() / ".docmanager"
        self.config_file = self.config_dir / "config.json"
        self.config: Dict[str, Any] = {}

        self._ensure_dir()
        self.load()

    def _ensure_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self):
        """加载配置"""
        defaults = {
            "theme": "dark",
            "language": "zh_CN",
            "auto_open_last": True,
            "last_library_id": None,
            "last_library_db_path": None,
            "recent_libraries": [],       # [{"id":1,"name":"xxx","db_path":"..."}]
            "window_geometry": None,      # [x, y, w, h]
            "copy_to_storage": True,
            "check_duplicate": True,
            "items_per_page": 500,
            "default_view": "list",
            "thumbnail_size": 128,
            "enable_preview": True,
            "log_level": "INFO",
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.config = {**defaults, **saved}
                logger.info("配置加载成功")
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                self.config = defaults
        else:
            self.config = defaults

    def save(self):
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """设置配置项"""
        self.config[key] = value
        self.save()

    # ── 最近打开库 ──────────────────────────────

    def add_recent_library(self, library_id: int, name: str, db_path: str):
        """添加到最近打开列表"""
        recent: List[dict] = self.config.get("recent_libraries", [])

        # 移除重复项
        recent = [r for r in recent if r.get("db_path") != db_path]

        # 插入到头部
        recent.insert(0, {
            "id": library_id,
            "name": name,
            "db_path": db_path
        })

        # 最多保留 10 条
        self.config["recent_libraries"] = recent[:10]

        # 同时更新 last_library
        self.config["last_library_id"] = library_id
        self.config["last_library_db_path"] = db_path

        self.save()

    def get_recent_libraries(self) -> List[dict]:
        """获取最近打开库列表"""
        recent = self.config.get("recent_libraries", [])

        # 过滤掉数据库文件不存在的记录
        valid = []
        for item in recent:
            db_path = item.get("db_path", "")
            if db_path and Path(db_path).exists():
                valid.append(item)

        if len(valid) != len(recent):
            self.config["recent_libraries"] = valid
            self.save()

        return valid

    def get_last_library(self) -> Optional[dict]:
        """获取上次打开的库"""
        recent = self.get_recent_libraries()
        return recent[0] if recent else None

    # ── 窗口状态 ────────────────────────────────

    def save_window_geometry(self, x: int, y: int, width: int, height: int):
        """保存窗口位置和大小"""
        self.config["window_geometry"] = [x, y, width, height]
        self.save()

    def get_window_geometry(self) -> Optional[list]:
        """获取窗口位置和大小"""
        return self.config.get("window_geometry")