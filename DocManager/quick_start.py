def main():
    """主函数"""
    db_path, library_id = create_test_library()
    
    if not db_path:
        print("无法创建测试库，退出")
        return
    
    print("\n启动 GUI...")
    
    # 1. 先创建 QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("DocManager")
    app.setOrganizationName("DocManager")
    app.setStyle("Fusion")  # 重要：必须在加载 QSS 之前设置
    
    # 2. 立即加载深色主题
    from utils.style_manager import StyleManager
    style_manager = StyleManager()
    style_manager.load_theme(StyleManager.DARK_THEME)
    
    # 3. 创建窗口
    from gui.main_window import MainWindow
    window = MainWindow()
    
    # 4. 打开测试库
    window.open_library(library_id, db_path)
    window.show()
    
    sys.exit(app.exec())