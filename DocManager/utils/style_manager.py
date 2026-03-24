"""
样式管理器（修复版）
"""
from pathlib import Path
from PyQt6.QtWidgets import QApplication
import logging

logger = logging.getLogger(__name__)


class StyleManager:
    """样式管理器"""
    
    DARK_THEME = "dark"
    LIGHT_THEME = "light"
    
    def __init__(self):
        self.current_theme = self.DARK_THEME
    
    def get_styles_dir(self) -> Path:
        """
        获取样式目录（兼容开发环境和打包后）
        """
        import sys
        
        # 打包后的路径
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)
        else:
            # 开发环境：从当前文件向上找到项目根目录
            base_path = Path(__file__).parent.parent
        
        styles_dir = base_path / "gui" / "styles"
        
        logger.info(f"样式目录: {styles_dir}")
        logger.info(f"样式目录存在: {styles_dir.exists()}")
        
        return styles_dir
    
    def load_theme(self, theme_name: str = DARK_THEME):
        """
        加载主题
        
        Args:
            theme_name: 主题名称（dark 或 light）
        """
        try:
            styles_dir = self.get_styles_dir()
            style_file = styles_dir / f"{theme_name}.qss"
            
            logger.info(f"加载样式文件: {style_file}")
            
            if not style_file.exists():
                logger.warning(f"样式文件不存在: {style_file}")
                logger.info("使用内置样式...")
                stylesheet = self.get_builtin_style(theme_name)
            else:
                with open(style_file, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                logger.info(f"样式文件加载成功，长度: {len(stylesheet)}")
            
            app = QApplication.instance()
            if app:
                app.setStyleSheet(stylesheet)
                self.current_theme = theme_name
                logger.info(f"主题应用成功: {theme_name}")
            else:
                logger.error("QApplication 实例不存在")
        
        except Exception as e:
            logger.error(f"加载主题失败: {e}", exc_info=True)
            # 失败时使用内置样式
            self.apply_builtin_style(theme_name)
    
    def apply_builtin_style(self, theme_name: str):
        """应用内置样式"""
        try:
            app = QApplication.instance()
            if app:
                stylesheet = self.get_builtin_style(theme_name)
                app.setStyleSheet(stylesheet)
                self.current_theme = theme_name
                logger.info(f"内置主题应用成功: {theme_name}")
        except Exception as e:
            logger.error(f"应用内置样式失败: {e}")
    
    def get_builtin_style(self, theme_name: str) -> str:
        """
        获取内置样式字符串（直接嵌入代码，不依赖文件）
        """
        if theme_name == self.DARK_THEME:
            return self._get_dark_style()
        else:
            return self._get_light_style()
    
    def _get_dark_style(self) -> str:
        """内置深色主题样式"""
        return """
/* DocManager 深色主题 */

QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "Microsoft YaHei UI", "Segoe UI", Arial, sans-serif;
    font-size: 9pt;
}

QMainWindow {
    background-color: #2b2b2b;
}

QDialog {
    background-color: #2b2b2b;
}

QMenuBar {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border-bottom: 1px solid #555555;
}

QMenuBar::item {
    padding: 5px 10px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #4a4a4a;
}

QMenuBar::item:pressed {
    background-color: #555555;
}

QMenu {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
}

QMenu::item {
    padding: 6px 25px 6px 20px;
}

QMenu::item:selected {
    background-color: #0d7377;
}

QMenu::separator {
    height: 1px;
    background-color: #555555;
    margin: 3px 0px;
}

QToolBar {
    background-color: #3c3c3c;
    border-bottom: 1px solid #555555;
    spacing: 5px;
    padding: 3px;
}

QToolButton {
    background-color: transparent;
    color: #e0e0e0;
    border: none;
    padding: 5px;
    border-radius: 4px;
}

QToolButton:hover {
    background-color: #4a4a4a;
}

QToolButton:pressed {
    background-color: #555555;
}

QStatusBar {
    background-color: #3c3c3c;
    color: #b0b0b0;
    border-top: 1px solid #555555;
}

QPushButton {
    background-color: #4a4a4a;
    color: #e0e0e0;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 6px 15px;
    min-width: 60px;
}

QPushButton:hover {
    background-color: #555555;
    border-color: #777777;
}

QPushButton:pressed {
    background-color: #3a3a3a;
}

QPushButton:disabled {
    background-color: #3c3c3c;
    color: #666666;
    border-color: #444444;
}

QPushButton:default {
    background-color: #0d7377;
    color: #ffffff;
    border-color: #0d7377;
}

QPushButton:default:hover {
    background-color: #0e8387;
}

QLineEdit {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #0d7377;
}

QLineEdit:focus {
    border-color: #0d7377;
}

QLineEdit:disabled {
    background-color: #2b2b2b;
    color: #666666;
}

QTextEdit {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    selection-background-color: #0d7377;
}

QTextEdit:focus {
    border-color: #0d7377;
}

QPlainTextEdit {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
}

QListWidget {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    outline: none;
}

QListWidget::item {
    padding: 5px 8px;
    border-radius: 3px;
}

QListWidget::item:selected {
    background-color: #0d7377;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #4a4a4a;
}

QTreeWidget {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    outline: none;
}

QTreeWidget::item {
    padding: 4px;
}

QTreeWidget::item:selected {
    background-color: #0d7377;
    color: #ffffff;
}

QTreeWidget::item:hover:!selected {
    background-color: #4a4a4a;
}

QTableWidget {
    background-color: #3c3c3c;
    color: #e0e0e0;
    gridline-color: #4a4a4a;
    border: 1px solid #555555;
    border-radius: 4px;
    outline: none;
    selection-background-color: #0d7377;
    selection-color: #ffffff;
    alternate-background-color: #383838;
}

QTableWidget::item {
    padding: 5px 8px;
}

QTableWidget::item:selected {
    background-color: #0d7377;
    color: #ffffff;
}

QHeaderView {
    background-color: #3c3c3c;
}

QHeaderView::section {
    background-color: #3c3c3c;
    color: #b0b0b0;
    border: none;
    border-right: 1px solid #555555;
    border-bottom: 1px solid #555555;
    padding: 6px 8px;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #4a4a4a;
    color: #e0e0e0;
}

QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 10px;
    border: none;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    min-height: 30px;
    border-radius: 5px;
    margin: 1px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar::handle:vertical:pressed {
    background-color: #0d7377;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
    border: none;
    background: none;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 10px;
    border: none;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    min-width: 30px;
    border-radius: 5px;
    margin: 1px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #666666;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
    border: none;
    background: none;
}

QComboBox {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 8px;
    min-width: 80px;
}

QComboBox:hover {
    border-color: #0d7377;
}

QComboBox:focus {
    border-color: #0d7377;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 10px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #e0e0e0;
}

QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    selection-background-color: #0d7377;
    outline: none;
}

QProgressBar {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #0d7377;
    border-radius: 3px;
}

QGroupBox {
    border: 1px solid #555555;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
    color: #b0b0b0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #b0b0b0;
    left: 10px;
}

QTabWidget::pane {
    border: 1px solid #555555;
    border-radius: 4px;
    background-color: #2b2b2b;
    top: -1px;
}

QTabBar::tab {
    background-color: #3c3c3c;
    color: #b0b0b0;
    border: 1px solid #555555;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border-bottom: 2px solid #0d7377;
}

QTabBar::tab:hover:!selected {
    background-color: #4a4a4a;
    color: #e0e0e0;
}

QSplitter::handle {
    background-color: #555555;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

QSplitter::handle:hover {
    background-color: #0d7377;
}

QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #666666;
    border-radius: 3px;
    background-color: #3c3c3c;
}

QCheckBox::indicator:checked {
    background-color: #0d7377;
    border-color: #0d7377;
}

QCheckBox::indicator:hover {
    border-color: #0d7377;
}

QRadioButton {
    color: #e0e0e0;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #666666;
    border-radius: 8px;
    background-color: #3c3c3c;
}

QRadioButton::indicator:checked {
    background-color: #0d7377;
    border-color: #0d7377;
}

QSpinBox, QDoubleSpinBox {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #0d7377;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: #4a4a4a;
    border: none;
    border-left: 1px solid #555555;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #555555;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #4a4a4a;
    border: none;
    border-left: 1px solid #555555;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #555555;
}

QDateEdit {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
}

QDateEdit:focus {
    border-color: #0d7377;
}

QDateEdit::drop-down {
    border: none;
    width: 20px;
}

QCalendarWidget {
    background-color: #3c3c3c;
    color: #e0e0e0;
}

QCalendarWidget QWidget {
    background-color: #3c3c3c;
    color: #e0e0e0;
}

QToolTip {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px;
}

QMessageBox {
    background-color: #2b2b2b;
}

QMessageBox QLabel {
    color: #e0e0e0;
}

QInputDialog {
    background-color: #2b2b2b;
}

QFileDialog {
    background-color: #2b2b2b;
}

QLabel {
    color: #e0e0e0;
    background-color: transparent;
}
"""
    
    def _get_light_style(self) -> str:
        """内置浅色主题样式"""
        return """
/* DocManager 浅色主题 */

QWidget {
    background-color: #f5f5f5;
    color: #333333;
    font-family: "Microsoft YaHei UI", "Segoe UI", Arial, sans-serif;
    font-size: 9pt;
}

QMainWindow {
    background-color: #ffffff;
}

QDialog {
    background-color: #f5f5f5;
}

QMenuBar {
    background-color: #f8f8f8;
    color: #333333;
    border-bottom: 1px solid #e0e0e0;
}

QMenuBar::item:selected {
    background-color: #e8e8e8;
}

QMenu {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
}

QMenu::item:selected {
    background-color: #0d7377;
    color: #ffffff;
}

QToolBar {
    background-color: #f8f8f8;
    border-bottom: 1px solid #e0e0e0;
}

QStatusBar {
    background-color: #f0f0f0;
    color: #666666;
    border-top: 1px solid #e0e0e0;
}

QPushButton {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px 15px;
}

QPushButton:hover {
    background-color: #f0f0f0;
    border-color: #0d7377;
}

QPushButton:default {
    background-color: #0d7377;
    color: #ffffff;
    border-color: #0d7377;
}

QLineEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 5px 8px;
}

QLineEdit:focus {
    border-color: #0d7377;
}

QTextEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
}

QTableWidget {
    background-color: #ffffff;
    color: #333333;
    gridline-color: #e0e0e0;
    border: 1px solid #d0d0d0;
    selection-background-color: #0d7377;
    selection-color: #ffffff;
    alternate-background-color: #fafafa;
}

QHeaderView::section {
    background-color: #f5f5f5;
    color: #666666;
    border-bottom: 1px solid #e0e0e0;
    padding: 6px 8px;
    font-weight: bold;
}

QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 10px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QLabel {
    color: #333333;
    background-color: transparent;
}

QGroupBox {
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    color: #666666;
}
"""
    
    def switch_theme(self):
        """切换主题"""
        new_theme = (
            self.LIGHT_THEME 
            if self.current_theme == self.DARK_THEME 
            else self.DARK_THEME
        )
        self.load_theme(new_theme)
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self.current_theme