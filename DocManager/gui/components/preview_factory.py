"""
预览组件工厂
"""
from pathlib import Path

from .text_preview import TextPreview
from .image_preview import ImagePreview
from .pdf_preview import PDFPreview
from .office_preview import OfficePreview
from .preview_base import PreviewWidget


class PreviewFactory:
    """预览组件工厂"""

    TEXT_EXT = {
        '.txt', '.md', '.log', '.json', '.xml', '.csv',
        '.py', '.java', '.cpp', '.h', '.c', '.js', '.ts',
        '.html', '.css', '.scss', '.sql', '.sh', '.bat',
        '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml',
        '.vue', '.jsx', '.tsx', '.go', '.rs', '.swift',
        '.kt', '.scala', '.rb', '.php', '.pl', '.lua',
        '.r', '.m', '.h', '.hpp', '.cs', '.vb', '.swift',
        '.dart', '.clj', '.ex', '.erl', '.hs', '.ml',
        '.ps1', '.vbs', '.asm', '.s', '.gradle', '.maven'
    }
    IMAGE_EXT = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
        '.ico', '.tiff', '.tif', '.svg', '.heic', '.heif'
    }
    PDF_EXT = {'.pdf'}
    OFFICE_EXT = {
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.odt', '.ods', '.odp', '.rtf'
    }

    @staticmethod
    def create_preview(file_path: str, parent=None) -> PreviewWidget:
        ext = Path(file_path).suffix.lower()
        if ext in PreviewFactory.IMAGE_EXT:
            return ImagePreview(parent)
        elif ext in PreviewFactory.PDF_EXT:
            return PDFPreview(parent)
        elif ext in PreviewFactory.OFFICE_EXT:
            return OfficePreview(parent)
        elif ext in PreviewFactory.TEXT_EXT:
            return TextPreview(parent)
        else:
            return TextPreview(parent)

    @staticmethod
    def is_previewable(file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        all_ext = (PreviewFactory.TEXT_EXT |
                   PreviewFactory.IMAGE_EXT |
                   PreviewFactory.PDF_EXT |
                   PreviewFactory.OFFICE_EXT)
        return ext in all_ext

    @staticmethod
    def get_supported_extensions() -> dict:
        return {
            '文本文件': list(PreviewFactory.TEXT_EXT),
            '图片文件': list(PreviewFactory.IMAGE_EXT),
            'PDF 文件': list(PreviewFactory.PDF_EXT),
            'Office 文档': list(PreviewFactory.OFFICE_EXT),
        }
