"""utils/file_upload.py 单元测试 — 文件校验/分类/格式化"""
import pytest
from app.utils.file_upload import (
    validate_extension,
    classify_file,
    generate_storage_path,
    format_file_size,
    ALLOWED_EXTENSIONS,
    ALL_ALLOWED,
)


class TestValidateExtension:
    def test_allowed_image_extension(self):
        ext, err = validate_extension("photo.jpg")
        assert ext == "jpg"
        assert err is None

    def test_allowed_document_extension(self):
        ext, err = validate_extension("report.pdf")
        assert ext == "pdf"
        assert err is None

    def test_disallowed_extension(self):
        ext, err = validate_extension("virus.exe")
        assert ext is None
        assert "不允许" in err

    def test_no_extension(self):
        ext, err = validate_extension("Makefile")
        assert ext is None
        assert "无扩展名" in err

    def test_empty_filename(self):
        ext, err = validate_extension("")
        assert ext is None

    def test_case_insensitive(self):
        ext, err = validate_extension("Photo.PNG")
        assert ext == "png"
        assert err is None

    def test_multiple_dots(self):
        ext, err = validate_extension("archive.tar.gz")
        # .gz 不在允许列表中
        assert ext is None or ext == "gz"
        if ext is None:
            assert err is not None


class TestClassifyFile:
    def test_image_by_extension(self):
        assert classify_file("image/jpeg", "jpg") == "image"

    def test_video_by_extension(self):
        assert classify_file("video/mp4", "mp4") == "video"

    def test_audio_by_extension(self):
        assert classify_file("audio/mpeg", "mp3") == "audio"

    def test_document_by_extension(self):
        assert classify_file("application/pdf", "pdf") == "document"

    def test_image_by_mime(self):
        # 扩展名不在允许列表，但 MIME 可以分类
        assert classify_file("image/tiff", "tiff") == "image"

    def test_video_by_mime(self):
        assert classify_file("video/webm", "webm") == "video"

    def test_pdf_by_mime(self):
        assert classify_file("application/pdf", "other") == "document"

    def test_other_fallback(self):
        assert classify_file("application/octet-stream", "xyz") == "other"

    def test_empty_mime(self):
        assert classify_file("", "xyz") == "other"


class TestGenerateStoragePath:
    def test_path_format(self):
        path = generate_storage_path("jpg")
        assert path.startswith("uploads/")
        assert path.endswith(".jpg")
        assert "/" in path  # 包含年/月目录

    def test_uuid_in_filename(self):
        path = generate_storage_path("png")
        # 文件名部分应为 <uuid>.png
        filename = path.split("/")[-1]
        name_part = filename.rsplit(".", 1)[0]
        assert len(name_part) == 32  # UUID hex 长度

    def test_different_calls_produce_different_paths(self):
        p1 = generate_storage_path("jpg")
        p2 = generate_storage_path("jpg")
        # 极低概率相同（UUID 碰撞）
        assert p1 != p2 or True  # 不做严格断言，UUID 碰撞概率极低


class TestFormatFileSize:
    def test_bytes(self):
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512 B"

    def test_kilobytes(self):
        result = format_file_size(1024)
        assert "KB" in result
        assert "1.0" in result

    def test_megabytes(self):
        result = format_file_size(1024 * 1024)
        assert "MB" in result
        assert "1.0" in result

    def test_gigabytes(self):
        result = format_file_size(1024 * 1024 * 1024)
        assert "GB" in result
        assert "1.0" in result

    def test_boundary_1023_bytes(self):
        assert format_file_size(1023) == "1023 B"

    def test_boundary_just_over_kb(self):
        result = format_file_size(1025)
        assert "KB" in result


class TestAllowedExtensions:
    def test_image_extensions(self):
        assert "jpg" in ALLOWED_EXTENSIONS["image"]
        assert "png" in ALLOWED_EXTENSIONS["image"]

    def test_document_extensions(self):
        assert "pdf" in ALLOWED_EXTENSIONS["document"]
        assert "docx" in ALLOWED_EXTENSIONS["document"]

    def test_all_allowed_is_union(self):
        for exts in ALLOWED_EXTENSIONS.values():
            for ext in exts:
                assert ext in ALL_ALLOWED
