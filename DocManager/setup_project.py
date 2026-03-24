"""
DocManager 项目初始化脚本
运行此脚本创建完整项目结构
"""
import os
from pathlib import Path

def create_project_structure():
    """创建项目目录结构"""
    
    base_dir = Path("docmanager")
    
    # 定义目录结构
    directories = [
        "core",
        "gui",
        "gui/components",
        "gui/dialogs",
        "gui/styles",
        "utils",
        "assets",
        "assets/icons",
        "assets/images",
        "tests",
        "build",
        "docs",
    ]
    
    # 创建目录
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # 创建 __init__.py
        if not directory.startswith("assets") and not directory.startswith("build") and not directory.startswith("docs"):
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""DocManager - 文档管家"""\n')
    
    print("✓ 项目目录结构创建完成")
    
    # 创建主要文件
    files_to_create = {
        "main.py": get_main_template(),
        "requirements.txt": get_requirements_template(),
        "README.md": get_readme_template(),
        ".gitignore": get_gitignore_template(),
        "core/schema.sql": "",  # 后续填充
    }
    
    for file_path, content in files_to_create.items():
        full_path = base_dir / file_path
        if not full_path.exists():
            full_path.write_text(content, encoding='utf-8')
    
    print("✓ 项目文件创建完成")
    print(f"\n项目已创建在: {base_dir.absolute()}")
    print("\n下一步:")
    print("1. cd docmanager")
    print("2. python -m venv venv")
    print("3. venv\\Scripts\\activate  (Windows)")
    print("4. pip install -r requirements.txt")

def get_main_template():
    return '''"""
DocManager - 文档管家
主程序入口
"""
import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DocManager")
    app.setOrganizationName("DocManager")
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
'''

def get_requirements_template():
    return '''# DocManager 依赖包
PyQt6>=6.5.0
watchdog>=3.0.0
Pillow>=10.0.0
python-magic-bin>=0.4.14
'''

def get_readme_template():
    return '''# DocManager（文档管家）

面向小团队的文档分类管理系统

## 功能特性

- 📁 库管理：统一管理文档库
- 📥 文档导入：批量导入，自动去重
- 🏷️ 分类与标签：灵活的组织方式
- 🔍 智能搜索：快速定位文档
- 🤖 智能文件夹：基于规则自动聚合
- 🔄 去重管理：识别重复文档
- 📋 待整理中心：集中治理未归档文档

## 技术栈

- Python 3.11+
- PyQt6
- SQLite

## 安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\\Scripts\\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```
'''

def get_gitignore_template():
    return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 虚拟环境
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 项目特定
docmanager.db
*.db
uploads/
'''

if __name__ == "__main__":
    create_project_structure()
