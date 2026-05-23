import os
import uuid
from datetime import datetime
from pathlib import Path

import magic

from app.settings import settings

# 允许上传的扩展名分类
ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "image": {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"},
    "document": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "md"},
    "video": {"mp4", "avi", "mov", "mkv", "wmv", "flv"},
    "audio": {"mp3", "wav", "ogg", "flac", "aac"},
}

ALL_ALLOWED = set().union(*ALLOWED_EXTENSIONS.values())


def validate_extension(filename: str) -> tuple[str | None, str | None]:
    """校验文件扩展名是否允许，返回 (extension, error_msg)"""
    if not filename or "." not in filename:
        return None, "文件名无扩展名"
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALL_ALLOWED:
        return None, f"不允许的文件类型: .{ext}"
    return ext, None


def detect_mime(file_path: str) -> str:
    """使用 python-magic 检测真实 MIME 类型"""
    return magic.from_file(file_path, mime=True) or "application/octet-stream"


def classify_file(mime_type: str, extension: str) -> str:
    """根据 MIME 类型和扩展名分类文件"""
    for category, exts in ALLOWED_EXTENSIONS.items():
        if extension in exts:
            return category
    mime_prefix = mime_type.split("/")[0] if mime_type else ""
    if mime_prefix in ("image", "video", "audio"):
        return mime_prefix
    if mime_type == "application/pdf" or "word" in mime_type or "spreadsheet" in mime_type:
        return "document"
    return "other"


def generate_storage_path(extension: str) -> str:
    """生成存储相对路径: uploads/YYYY/MM/<uuid>.ext"""
    now = datetime.now()
    dir_path = f"uploads/{now.strftime('%Y')}/{now.strftime('%m')}"
    filename = f"{uuid.uuid4().hex}.{extension}"
    return os.path.join(dir_path, filename)


def ensure_storage_dir(storage_path: str) -> str:
    """确保存储目录存在，返回绝对路径"""
    abs_path = os.path.join(settings.STATIC_PATH, storage_path)
    Path(abs_path).parent.mkdir(parents=True, exist_ok=True)
    return abs_path


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
