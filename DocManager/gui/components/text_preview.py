"""
文本文件预览
"""
from PyQt6.QtWidgets import QVBoxLayout, QTextEdit
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression
from pathlib import Path
import logging

from .preview_base import PreviewWidget

logger = logging.getLogger(__name__)


class CodeHighlighter(QSyntaxHighlighter):
    """代码语法高亮"""

    KEYWORDS = {
        'python': ['def', 'class', 'import', 'from', 'return', 'if', 'else', 'elif',
                   'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'yield',
                   'lambda', 'pass', 'break', 'continue', 'True', 'False', 'None',
                   'and', 'or', 'not', 'in', 'is', 'async', 'await'],
        'javascript': ['function', 'const', 'let', 'var', 'return', 'if', 'else',
                       'for', 'while', 'class', 'import', 'export', 'from', 'async',
                       'await', 'try', 'catch', 'finally', 'new', 'this', 'super',
                       'true', 'false', 'null', 'undefined'],
        'java': ['public', 'private', 'protected', 'class', 'interface', 'extends',
                 'implements', 'return', 'if', 'else', 'for', 'while', 'try', 'catch',
                 'finally', 'new', 'this', 'super', 'static', 'final', 'void',
                 'true', 'false', 'null'],
        'cpp': ['int', 'float', 'double', 'char', 'void', 'class', 'struct',
                'public', 'private', 'protected', 'return', 'if', 'else', 'for',
                'while', 'try', 'catch', 'new', 'delete', 'const', 'static',
                'virtual', 'override', 'true', 'false', 'nullptr'],
        'sql': ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
                'ON', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'ORDER', 'BY', 'GROUP',
                'HAVING', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'TABLE', 'DROP',
                'INDEX', 'VIEW', 'NULL', 'TRUE', 'FALSE'],
    }

    def __init__(self, document, language='python'):
        super().__init__(document)
        self.language = language
        self.init_formats()
        self.init_rules()

    def init_formats(self):
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor('#569cd6'))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor('#ce9178'))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor('#6a9955'))

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor('#b5cea8'))

        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor('#dcdcaa'))

    def init_rules(self):
        self.highlighting_rules = []

        keywords = self.KEYWORDS.get(self.language, self.KEYWORDS['python'])
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, self.keyword_format))

        self.highlighting_rules.append((
            QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'),
            self.string_format
        ))
        self.highlighting_rules.append((
            QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"),
            self.string_format
        ))

        if self.language in ['python']:
            self.highlighting_rules.append((
                QRegularExpression(r'#[^\n]*'),
                self.comment_format
            ))
        else:
            self.highlighting_rules.append((
                QRegularExpression(r'//[^\n]*'),
                self.comment_format
            ))

        self.highlighting_rules.append((
            QRegularExpression(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/'),
            self.comment_format
        ))

        self.highlighting_rules.append((
            QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'),
            self.number_format
        ))

        self.highlighting_rules.append((
            QRegularExpression(r'\b[a-zA-Z_][a-zA-Z0-9_]*(?=\s*\()'),
            self.function_format
        ))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(
                    match.capturedStart(),
                    match.capturedLength(),
                    format
                )


class TextPreview(PreviewWidget):
    """文本预览"""

    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'javascript',
        '.jsx': 'javascript',
        '.tsx': 'javascript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'cpp',
        '.h': 'cpp',
        '.hpp': 'cpp',
        '.cs': 'java',
        '.sql': 'sql',
    }

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont('Consolas', 10))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
        """)
        layout.addWidget(self.text_edit)

        self.highlighter = None

    def do_preview(self, file_path: str):
        try:
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            content = None
            for enc in encodings:
                try:
                    content = Path(file_path).read_text(encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                self.text_edit.setPlainText("无法解码文件内容")
                return

            if len(content) > 100000:
                content = content[:100000] + "\n\n... (内容过长，仅显示前100KB)"

            self.text_edit.setPlainText(content)

            ext = Path(file_path).suffix.lower()
            language = self.LANGUAGE_MAP.get(ext)
            if language:
                self.highlighter = CodeHighlighter(self.text_edit.document(), language)

        except Exception as e:
            logger.error(f"预览文本失败: {e}")
            self.text_edit.setPlainText(f"预览失败: {e}")

    def clear(self):
        self.text_edit.clear()
        self.highlighter = None
        self.current_file = None
