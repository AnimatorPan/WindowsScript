"""
DocManager 主程序入口（最终版）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRect
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('docmanager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("DocManager")
        app.setApplicationDisplayName("DocManager - 文档管家")
        app.setOrganizationName("DocManager")
        app.setStyle("Fusion")

        # 加载主题
        from utils.style_manager import StyleManager
        from utils.config_manager import ConfigManager

        config = ConfigManager()
        theme = config.get("theme", "dark")

        style_manager = StyleManager()
        style_manager.load_theme(theme)

        # 创建主窗口
        from gui.main_window import MainWindow

        window = MainWindow()

        # 恢复窗口大小位置
        geo = config.get_window_geometry()
        if geo and len(geo) == 4:
            window.setGeometry(QRect(geo[0], geo[1], geo[2], geo[3]))
        else:
            window.setGeometry(100, 100, 1400, 900)

        window.show()

        # 尝试恢复上次打开的库，失败则弹欢迎页
        if not window.try_restore_last_library():
            window.show_welcome()

        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()