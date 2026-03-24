"""
创建库对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QPushButton, QFileDialog, QHBoxLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt
from pathlib import Path


class CreateLibraryDialog(QDialog):
    """创建库对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.library_info = {}
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("创建新库")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 表单
        form_layout = QFormLayout()
        
        # 库名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如: 我的文档库")
        form_layout.addRow("库名称:", self.name_edit)
        
        # 存储路径
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择文档存储位置")
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        
        form_layout.addRow("存储路径:", path_layout)
        
        # 描述
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("可选：添加库的描述信息")
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("描述:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("创建")
        create_btn.setDefault(True)
        create_btn.clicked.connect(self.on_create)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
    
    def browse_path(self):
        """选择路径"""
        path = QFileDialog.getExistingDirectory(
            self,
            "选择存储目录",
            str(Path.home())
        )
        
        if path:
            self.path_edit.setText(path)
    
    def on_create(self):
        """创建"""
        name = self.name_edit.text().strip()
        path = self.path_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        
        # 验证
        if not name:
            QMessageBox.warning(self, "提示", "请输入库名称")
            self.name_edit.setFocus()
            return
        
        if not path:
            QMessageBox.warning(self, "提示", "请选择存储路径")
            return
        
        # 保存信息
        self.library_info = {
            'name': name,
            'storage_path': path,
            'description': description
        }
        
        self.accept()
    
    def get_library_info(self):
        """获取库信息"""
        return self.library_info