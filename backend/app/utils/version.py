"""版本工具"""
from pathlib import Path


def get_version():
    """获取项目版本"""
    try:
        version_file = Path(__file__).parent.parent.parent.parent / "VERSION"
        return version_file.read_text().strip()
    except Exception:
        return "unknown"
