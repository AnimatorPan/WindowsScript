# DocManager 项目开发状态文档

> 本文档记录项目当前开发状态、代码结构、后续开发计划，供后续开发参考。

---

## 一、项目概述

### 1.1 项目定位
DocManager 是一款面向小团队的文档管理工具，解决以下问题：
- 文档分散、难以查找
- 分类混乱、标签不规范
- 重复文件占用空间
- 缺乏统一的文档治理流程

### 1.2 技术栈
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 主要开发语言 |
| PyQt6 | 6.x | GUI 框架 |
| SQLite | 3.x | 本地数据库 |
| watchdog | 3.x | 文件监控 |

### 1.3 运行方式
```bash
cd g:\GitHub\WindowsScript\docmanager
python main.py
```

---

## 二、项目结构

```
docmanager/
├── main.py                    # 应用入口
├── config.json                # 配置文件
├── docmanager.db              # SQLite 数据库
│
├── core/                      # 核心业务逻辑
│   ├── __init__.py
│   ├── database.py            # 数据库管理
│   ├── document.py            # 文档管理
│   ├── category.py            # 分类管理
│   ├── tag.py                 # 标签管理
│   ├── library.py             # 库管理
│   ├── search.py              # 搜索引擎
│   ├── smart_folder.py        # 智能文件夹
│   ├── duplicate_detector.py  # 去重检测
│   ├── statistics.py          # 统计分析
│   ├── file_watcher.py        # 文件监控
│   └── preview/               # 预览模块
│       ├── __init__.py
│       ├── preview_factory.py # 预览工厂
│       ├── base_preview.py    # 预览基类
│       ├── text_preview.py    # 文本预览
│       ├── image_preview.py   # 图片预览
│       └── pdf_preview.py     # PDF 预览
│
├── gui/                       # 图形界面
│   ├── __init__.py
│   ├── main_window.py         # 主窗口
│   ├── welcome_dialog.py      # 欢迎页
│   ├── unorganized_center.py  # 待整理中心
│   ├── statistics_window.py   # 统计窗口
│   ├── styles/                # 样式文件
│   │   ├── dark.qss           # 深色主题
│   │   └── light.qss          # 浅色主题
│   ├── components/            # UI 组件
│   │   ├── sidebar.py         # 侧边栏
│   │   ├── document_area.py   # 文档区域
│   │   ├── detail_panel.py    # 详情面板
│   │   └── toolbar.py         # 工具栏
│   └── dialogs/               # 对话框
│       ├── import_dialog.py   # 导入对话框
│       ├── category_dialog.py # 分类管理
│       ├── tag_dialog.py      # 标签管理
│       ├── search_dialog.py   # 高级搜索
│       ├── smart_folder_dialog.py # 智能文件夹
│       └── duplicate_handler_dialog.py # 去重处理
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── config_manager.py      # 配置管理
│   ├── style_manager.py       # 样式管理
│   └── file_utils.py          # 文件工具
│
└── tests/                     # 测试文件
    ├── test_database.py
    ├── test_document.py
    └── test_duplicate_detector.py
```

---

## 三、数据库结构

### 3.1 核心表

```sql
-- 文档库
CREATE TABLE libraries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    library_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    file_hash TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    note TEXT,
    is_duplicate INTEGER DEFAULT 0,
    FOREIGN KEY (library_id) REFERENCES libraries(id)
);

-- 分类
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    library_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    parent_id INTEGER,
    description TEXT,
    FOREIGN KEY (library_id) REFERENCES libraries(id),
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

-- 标签
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    library_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#3498db',
    parent_id INTEGER,
    FOREIGN KEY (library_id) REFERENCES libraries(id),
    FOREIGN KEY (parent_id) REFERENCES tags(id)
);

-- 文档-分类关联
CREATE TABLE document_categories (
    document_id INTEGER,
    category_id INTEGER,
    PRIMARY KEY (document_id, category_id)
);

-- 文档-标签关联
CREATE TABLE document_tags (
    document_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (document_id, tag_id)
);

-- 智能文件夹
CREATE TABLE smart_folders (
    id INTEGER PRIMARY KEY,
    library_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    rules TEXT NOT NULL,  -- JSON 格式存储规则
    is_enabled INTEGER DEFAULT 1,
    FOREIGN KEY (library_id) REFERENCES libraries(id)
);
```

---

## 四、已完成功能清单

### 4.1 MVP 功能（已完成 95%+）

| 模块 | 功能点 | 状态 |
|------|--------|------|
| **库管理** | 创建/打开库 | ✅ |
| | 库信息展示 | ✅ |
| **文档导入** | 导入单个文件 | ✅ |
| | 导入文件夹 | ✅ |
| | 导入进度显示 | ✅ |
| | 导入结果反馈 | ✅ |
| **文档浏览** | 列表视图 | ✅ |
| | 缩略图视图 | ✅ |
| | 视图切换 | ✅ |
| | 排序功能 | ✅ |
| | 多选文档 | ✅ |
| **分类管理** | 创建/编辑/删除分类 | ✅ |
| | 层级分类 | ✅ |
| | 文档归类 | ✅ |
| | 批量归类 | ✅ |
| **标签管理** | 创建/编辑/删除标签 | ✅ |
| | 层级标签 | ✅ |
| | 标签颜色 | ✅ |
| | 多标签绑定 | ✅ |
| | 批量打标签 | ✅ |
| **搜索筛选** | 全局搜索 | ✅ |
| | 文件名搜索 | ✅ |
| | 属性筛选 | ✅ |
| | 高级搜索 | ✅ |
| | 二次筛选 | ✅ |
| **智能文件夹** | 创建规则 | ✅ |
| | 条件组合 (AND/OR) | ✅ |
| | 规则类型：文件类型/名称/时间/标签 | ✅ |
| **文档详情** | 基础信息展示 | ✅ |
| | 分类/标签编辑 | ✅ |
| | 备注功能 | ✅ |
| | 文件预览 | ✅ |
| **去重管理** | 完全重复检测 (哈希) | ✅ |
| | 文件名相似检测 | ✅ |
| | 去重处理对话框 | ✅ |
| **待整理中心** | 未分类文档列表 | ✅ |
| | 未标签文档列表 | ✅ |
| | 疑似重复文档列表 | ✅ |
| | 批量分类/标签 | ✅ |
| **批量操作** | 批量归类 | ✅ |
| | 批量打标签 | ✅ |
| **系统** | 深色/浅色主题 | ✅ |
| | 统计窗口 | ✅ |

---

## 五、关键代码说明

### 5.1 主窗口初始化流程

```python
# main_window.py
class MainWindow(QMainWindow):
    def __init__(self, library_path):
        # 1. 初始化数据库
        self.db = Database(library_path)
        
        # 2. 获取当前库
        self.current_library = self.db.get_library_by_path(library_path)
        
        # 3. 初始化各管理器
        self.doc_manager = DocumentManager(self.db, self.library_id)
        self.category_manager = CategoryManager(self.db, self.library_id)
        self.tag_manager = TagManager(self.db, self.library_id)
        
        # 4. 构建 UI
        self.init_ui()
        
        # 5. 加载数据
        self.load_documents()
```

### 5.2 文档导入流程

```python
# 导入对话框 -> 文档管理器 -> 数据库
def import_files(self, file_paths):
    for path in file_paths:
        # 1. 计算文件哈希
        file_hash = self.calculate_hash(path)
        
        # 2. 检查重复
        if self.check_duplicate(file_hash):
            duplicates.append(path)
            continue
        
        # 3. 提取元信息
        doc_info = self.extract_metadata(path)
        
        # 4. 存入数据库
        self.db.insert_document(doc_info)
```

### 5.3 智能文件夹规则格式

```json
{
  "logic": "AND",
  "conditions": [
    {"field": "file_type", "operator": "equals", "value": "pdf"},
    {"field": "filename", "operator": "contains", "value": "报告"},
    {"field": "imported_at", "operator": "in_range", "value": {"start": "2024-01-01", "end": "2024-12-31"}}
  ]
}
```

### 5.4 去重检测算法

```python
# 完全重复：基于文件哈希
def find_exact_duplicates(self):
    # 查找相同哈希的文档组
    sql = """
        SELECT file_hash, COUNT(*) as count 
        FROM documents 
        WHERE library_id = ? AND file_hash IS NOT NULL
        GROUP BY file_hash 
        HAVING count > 1
    """

# 文件名相似：使用 difflib
def calculate_name_similarity(self, name1, name2):
    from difflib import SequenceMatcher
    stem1 = Path(name1).stem.lower()
    stem2 = Path(name2).stem.lower()
    return SequenceMatcher(None, stem1, stem2).ratio()
```

---

## 六、后续开发计划

### 6.1 第二版：效率提升（优先级高）

#### 6.1.1 回收站功能
**目标**：删除文档不直接消失，可恢复

**实现方案**：
1. 数据库增加 `is_deleted` 和 `deleted_at` 字段
2. 删除操作改为软删除（设置标记）
3. 新增回收站页面，展示已删除文档
4. 提供恢复和永久删除功能

**涉及文件**：
- `core/database.py` - 添加字段迁移
- `core/document.py` - 修改删除逻辑
- `gui/dialogs/trash_dialog.py` - 新建回收站对话框
- `gui/main_window.py` - 添加回收站入口

#### 6.1.2 归档功能
**目标**：长期不用的文档可归档，不占用主列表

**实现方案**：
1. 数据库增加 `is_archived` 字段
2. 归档文档默认不显示在主列表
3. 新增归档页面查看已归档文档

#### 6.1.3 工作台首页
**目标**：提供系统概览和快捷入口

**内容**：
- 最近导入文档
- 待整理数量统计
- 常用智能文件夹
- 最近搜索历史

**涉及文件**：
- `gui/components/dashboard.py` - 新建工作台组件
- `gui/main_window.py` - 集成工作台

#### 6.1.4 全文搜索
**目标**：搜索文档内容，不仅是文件名

**技术方案**：
- 使用 `whoosh` 或 `sqlite FTS5` 建立全文索引
- 支持 PDF、Word、TXT 等格式内容提取

#### 6.1.5 保存搜索条件
**目标**：常用搜索条件可保存复用

**实现方案**：
1. 新建 `saved_searches` 表存储搜索条件
2. 侧边栏增加"已保存搜索"区域
3. 点击快速执行搜索

### 6.2 第三版：治理升级

| 功能 | 说明 | 复杂度 |
|------|------|--------|
| 版本管理 | 文档版本链、版本标记 | 中等 |
| 统计报表 | 导入趋势、分类分布图表 | 中等 |
| 操作日志 | 记录用户操作历史 | 简单 |
| 用户权限 | 多用户、角色权限 | 复杂 |

### 6.3 第四版：智能化

| 功能 | 说明 | 复杂度 |
|------|------|--------|
| AI 自动分类 | 基于内容建议分类 | 复杂 |
| AI 标签推荐 | 自动生成标签建议 | 复杂 |
| 文档摘要 | 自动提取摘要 | 中等 |
| 云盘集成 | 同步外部数据源 | 复杂 |

---

## 七、已知问题与注意事项

### 7.1 已知问题
1. 大量文档（>10000）时列表加载较慢，需优化
2. PDF 预览依赖外部库，部分系统可能需要额外安装
3. 文件监控在 Windows 下可能有延迟

### 7.2 开发注意事项
1. **数据库字段名**：使用 `imported_at` 而非 `import_date`，使用 `note` 而非 `notes`
2. **方法命名**：
   - `DocumentManager.get_categories()` 获取文档分类
   - `DocumentManager.get_tags()` 获取文档标签
   - `StatisticsManager.get_category_stats()` 获取分类统计
3. **PyQt6 兼容性**：
   - `QKeySequence.New` 改为 `QKeySequence("Ctrl+N")`
   - 使用 `QMessageBox.StandardButton.Yes`
4. **深色主题**：设置背景色时需同时设置前景色，确保可读性

### 7.3 代码风格
- 不添加注释（除非用户要求）
- 使用中文界面文本
- 遵循 PEP 8 规范

---

## 八、测试方法

### 8.1 单元测试
```bash
cd g:\GitHub\WindowsScript\docmanager
python -m pytest tests/
```

### 8.2 手动测试
```bash
python main.py
```

### 8.3 创建测试数据
```bash
python create_sample_data.py
```

---

## 九、部署说明

### 9.1 打包为可执行文件
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name DocManager main.py
```

### 9.2 依赖安装
```bash
pip install PyQt6 watchdog
```

---

## 十、联系与维护

- 项目路径：`g:\GitHub\WindowsScript\docmanager`
- 配置文件：`config.json`
- 数据库：`docmanager.db`

---

*文档更新时间：2026-03-24*
