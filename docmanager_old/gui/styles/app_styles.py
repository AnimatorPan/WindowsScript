"""
应用样式定义 - Visual Studio 2019 Dark 主题
"""

# VS2019 Dark 配色方案
COLORS = {
    # 主背景色
    'bg_primary': '#1e1e1e',      # 主背景 (最深)
    'bg_secondary': '#252526',     # 侧边栏/面板背景
    'bg_tertiary': '#2d2d30',      # 输入框/卡片背景
    'bg_hover': '#3e3e42',         # 悬停背景 (更明显)
    'bg_selected': '#094771',      # 选中项背景 (VS蓝色)
    'bg_button': '#0e639c',        # 按钮背景 (VS蓝)
    
    # 文字颜色
    'text_primary': '#cccccc',     # 主要文字
    'text_secondary': '#a0a0a0',   # 次要文字 (更亮)
    'text_disabled': '#656565',    # 禁用文字
    'text_highlight': '#ffffff',   # 高亮文字
    
    # 边框颜色
    'border': '#3e3e42',           # 边框
    'border_light': '#5a5a5a',     # 亮边框
    'border_hover': '#007acc',     # 悬停边框 (VS蓝色)
    
    # 强调色
    'accent': '#007acc',           # VS蓝色
    'accent_hover': '#1177bb',     # 悬停蓝色
    'accent_light': '#1c97ea',     # 亮蓝色
    
    # 功能色
    'success': '#4ec9b0',          # 成功绿
    'warning': '#dcdcaa',          # 警告黄
    'error': '#f48771',            # 错误红
}


# 主要按钮样式 (蓝色背景，白色文字)
PRIMARY_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['accent']};
        color: {COLORS['text_highlight']};
        border: 1px solid {COLORS['accent']};
        padding: 8px 16px;
        border-radius: 2px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_hover']};
        border-color: {COLORS['accent_hover']};
    }}
    QPushButton:pressed {{
        background-color: {COLORS['accent']};
    }}
    QPushButton:disabled {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_disabled']};
        border-color: {COLORS['border']};
    }}
"""

# 默认按钮样式 (灰色背景，浅色文字)
DEFAULT_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 8px 16px;
        border-radius: 2px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['bg_hover']};
        border-color: {COLORS['border_light']};
        color: {COLORS['text_highlight']};
    }}
    QPushButton:pressed {{
        background-color: {COLORS['bg_secondary']};
    }}
"""

# 工具栏按钮样式 (透明背景，带悬停效果)
TOOLBAR_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLORS['text_primary']};
        border: 1px solid transparent;
        padding: 8px 12px;
        text-align: left;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['bg_hover']};
        border-color: {COLORS['border']};
        color: {COLORS['text_highlight']};
    }}
    QPushButton:checked {{
        background-color: {COLORS['bg_selected']};
        border-color: {COLORS['accent']};
        color: {COLORS['text_highlight']};
    }}
"""

# 侧边栏按钮样式 (带背景，更明显)
SIDEBAR_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 10px 16px;
        text-align: left;
        font-size: 13px;
        border-radius: 3px;
        margin: 2px 0px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['bg_hover']};
        border-color: {COLORS['border_light']};
        color: {COLORS['text_highlight']};
    }}
    QPushButton:checked {{
        background-color: {COLORS['bg_selected']};
        border-color: {COLORS['accent']};
        color: {COLORS['text_highlight']};
    }}
"""

# 输入框样式
LINE_EDIT_STYLE = f"""
    QLineEdit {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 8px 12px;
        border-radius: 2px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border-color: {COLORS['accent']};
    }}
    QLineEdit:disabled {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_disabled']};
    }}
"""

# 文本框样式
TEXT_EDIT_STYLE = f"""
    QTextEdit {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 8px;
        border-radius: 2px;
        font-size: 13px;
    }}
    QTextEdit:focus {{
        border-color: {COLORS['accent']};
    }}
"""

# 列表样式
LIST_WIDGET_STYLE = f"""
    QListWidget {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        min-height: 50px;
        max-height: 50px;
        padding: 0px 12px;
        border-radius: 3px;
        margin: 2px 0px;
        border: 1px solid transparent;
    }}
    QListWidget::item:hover {{
        background-color: {COLORS['bg_hover']};
        border-color: {COLORS['border']};
    }}
    QListWidget::item:selected {{
        background-color: {COLORS['bg_selected']};
        border-color: {COLORS['accent']};
        color: {COLORS['text_highlight']};
    }}
"""

# 表格样式
TABLE_WIDGET_STYLE = f"""
    QTableWidget {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        gridline-color: {COLORS['border']};
        outline: none;
    }}
    QTableWidget::item {{
        padding: 10px 12px;
        border-bottom: 1px solid {COLORS['border']};
    }}
    QTableWidget::item:selected {{
        background-color: {COLORS['bg_selected']};
        color: {COLORS['text_highlight']};
    }}
    QHeaderView::section {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        padding: 10px 12px;
        border: none;
        border-bottom: 1px solid {COLORS['border']};
        border-right: 1px solid {COLORS['border']};
        font-weight: 600;
    }}
"""

# 树形控件样式
TREE_WIDGET_STYLE = f"""
    QTreeWidget {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        outline: none;
    }}
    QTreeWidget::item {{
        padding: 8px 12px;
        border-radius: 2px;
    }}
    QTreeWidget::item:hover {{
        background-color: {COLORS['bg_hover']};
    }}
    QTreeWidget::item:selected {{
        background-color: {COLORS['bg_selected']};
        color: {COLORS['text_highlight']};
    }}
"""

# 分组框样式
GROUP_BOX_STYLE = f"""
    QGroupBox {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 16px;
        padding: 16px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
        color: {COLORS['text_highlight']};
    }}
"""

# 下拉框样式
COMBO_BOX_STYLE = f"""
    QComboBox {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 6px 12px;
        border-radius: 2px;
        min-width: 80px;
    }}
    QComboBox:hover {{
        border-color: {COLORS['border_light']};
    }}
    QComboBox:focus {{
        border-color: {COLORS['accent']};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left: 1px solid {COLORS['border']};
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        selection-background-color: {COLORS['bg_selected']};
    }}
"""

# 复选框样式
CHECK_BOX_STYLE = f"""
    QCheckBox {{
        color: {COLORS['text_primary']};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLORS['border']};
        background-color: {COLORS['bg_primary']};
        border-radius: 2px;
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent']};
        border-color: {COLORS['accent']};
    }}
    QCheckBox::indicator:hover {{
        border-color: {COLORS['border_light']};
    }}
"""

# 单选框样式
RADIO_BUTTON_STYLE = f"""
    QRadioButton {{
        color: {COLORS['text_primary']};
        spacing: 8px;
    }}
    QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLORS['border']};
        background-color: {COLORS['bg_primary']};
        border-radius: 8px;
    }}
    QRadioButton::indicator:checked {{
        background-color: {COLORS['accent']};
        border-color: {COLORS['accent']};
    }}
"""

# 滚动条样式
SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        background-color: {COLORS['bg_secondary']};
        width: 14px;
        border-left: 1px solid {COLORS['border']};
    }}
    QScrollBar::handle:vertical {{
        background-color: {COLORS['bg_tertiary']};
        min-height: 30px;
        border-radius: 0px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['border_light']};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {COLORS['bg_secondary']};
        height: 14px;
        border-top: 1px solid {COLORS['border']};
    }}
    QScrollBar::handle:horizontal {{
        background-color: {COLORS['bg_tertiary']};
        min-width: 30px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['border_light']};
    }}
"""

# 菜单栏样式
MENU_BAR_STYLE = f"""
    QMenuBar {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border-bottom: 1px solid {COLORS['border']};
    }}
    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 12px;
    }}
    QMenuBar::item:selected {{
        background-color: {COLORS['bg_selected']};
        color: {COLORS['text_highlight']};
    }}
    QMenuBar::item:pressed {{
        background-color: {COLORS['accent']};
    }}
"""

# 菜单样式
MENU_STYLE = f"""
    QMenu {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px;
        background-color: transparent;
    }}
    QMenu::item:selected {{
        background-color: {COLORS['bg_selected']};
        color: {COLORS['text_highlight']};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {COLORS['border']};
        margin: 4px 8px;
    }}
"""

# 状态栏样式
STATUS_BAR_STYLE = f"""
    QStatusBar {{
        background-color: {COLORS['accent']};
        color: {COLORS['text_highlight']};
        border-top: 1px solid {COLORS['border']};
    }}
    QStatusBar::item {{
        border: none;
    }}
"""

# 对话框样式
DIALOG_STYLE = f"""
    QDialog {{
        background-color: {COLORS['bg_primary']};
    }}
"""

# 标签样式
LABEL_TITLE_STYLE = f"color: {COLORS['text_highlight']}; font-size: 22px; font-weight: 600;"
LABEL_SUBTITLE_STYLE = f"color: {COLORS['text_secondary']}; font-size: 14px;"
LABEL_CAPTION_STYLE = f"color: {COLORS['text_disabled']}; font-size: 12px;"
LABEL_PRIMARY_STYLE = f"color: {COLORS['text_primary']}; font-size: 13px;"

# 分割器样式
SPLITTER_STYLE = f"""
    QSplitter::handle {{
        background-color: {COLORS['border']};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}
"""


def get_app_stylesheet() -> str:
    """获取完整应用样式表 - VS2019 Dark主题"""
    return (
        DIALOG_STYLE +
        MENU_BAR_STYLE +
        MENU_STYLE +
        LINE_EDIT_STYLE +
        TEXT_EDIT_STYLE +
        LIST_WIDGET_STYLE +
        TABLE_WIDGET_STYLE +
        TREE_WIDGET_STYLE +
        GROUP_BOX_STYLE +
        COMBO_BOX_STYLE +
        CHECK_BOX_STYLE +
        RADIO_BUTTON_STYLE +
        SCROLLBAR_STYLE +
        STATUS_BAR_STYLE +
        SPLITTER_STYLE
    )
