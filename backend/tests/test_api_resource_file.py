"""API 集成测试 — resource/file 路由（文件上传/列表/删除/预览/签名/统计）"""
import os
import pytest
from unittest.mock import patch

from app.models.file import File
from app.settings import settings


# ═══════════════════════════════════════════════════════════════════════
# 文件上传
# ═══════════════════════════════════════════════════════════════════════

class TestFileUploadAPI:
    def test_upload_valid_file(self, client, admin_headers, db, admin_user):
        """上传有效 PNG 文件"""
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        resp = client.post(
            "/api/v1/resource/file/upload",
            headers=admin_headers,
            files={"file": ("test_upload.png", png_content, "image/png")},
        )
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["name"] == "test_upload.png"

        # 清理磁盘文件
        if body["data"].get("path"):
            abs_path = os.path.join(settings.STATIC_PATH, body["data"]["path"])
            if os.path.exists(abs_path):
                os.remove(abs_path)

    def test_upload_invalid_extension(self, client, admin_headers, db, admin_user):
        """上传不允许的文件类型"""
        resp = client.post(
            "/api/v1/resource/file/upload",
            headers=admin_headers,
            files={"file": ("virus.exe", b"malware", "application/octet-stream")},
        )
        body = resp.json()
        assert body["code"] != 200


# ═══════════════════════════════════════════════════════════════════════
# 文件列表
# ═══════════════════════════════════════════════════════════════════════

class TestFileListAPI:
    def test_list_files(self, client, admin_headers, db, admin_user):
        """获取文件列表"""
        # 先创建一条文件记录
        file_obj = File(
            name="list_test.jpg", path="uploads/test/list_test.jpg",
            size=1024, mime_type="image/jpeg", file_type="image",
            extension="jpg", uploader_id=admin_user.id,
        )
        db.add(file_obj)
        db.commit()

        resp = client.post("/api/v1/resource/file/list", headers=admin_headers, json={
            "name": None, "file_type": None, "uploader_id": None,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["total"] >= 1

    def test_list_files_with_name_filter(self, client, admin_headers, db, admin_user):
        file_obj = File(
            name="unique_search_name.pdf", path="uploads/test/search.pdf",
            size=2048, mime_type="application/pdf", file_type="document",
            extension="pdf", uploader_id=admin_user.id,
        )
        db.add(file_obj)
        db.commit()

        resp = client.post("/api/v1/resource/file/list", headers=admin_headers, json={
            "name": "unique_search", "file_type": None, "uploader_id": None,
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["total"] >= 1

    def test_list_files_with_type_filter(self, client, admin_headers, db, admin_user):
        file_obj = File(
            name="type_filter.mp3", path="uploads/test/filter.mp3",
            size=4096, mime_type="audio/mpeg", file_type="audio",
            extension="mp3", uploader_id=admin_user.id,
        )
        db.add(file_obj)
        db.commit()

        resp = client.post("/api/v1/resource/file/list", headers=admin_headers, json={
            "name": None, "file_type": "audio", "uploader_id": None,
        })
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 文件更新/重命名
# ═══════════════════════════════════════════════════════════════════════

class TestFileUpdateAPI:
    def test_rename_file(self, client, admin_headers, db, admin_user):
        file_obj = File(
            name="old_name.jpg", path="uploads/test/rename.jpg",
            size=512, mime_type="image/jpeg", file_type="image",
            extension="jpg", uploader_id=admin_user.id,
        )
        db.add(file_obj)
        db.commit()
        db.refresh(file_obj)

        resp = client.post("/api/v1/resource/file/update", headers=admin_headers, json={
            "id": str(file_obj.id),
            "name": "new_name.jpg",
        })
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["name"] == "new_name.jpg"

    def test_rename_nonexistent_file(self, client, admin_headers, db):
        from uuid import uuid4
        resp = client.post("/api/v1/resource/file/update", headers=admin_headers, json={
            "id": str(uuid4()),
            "name": "ghost.jpg",
        })
        body = resp.json()
        assert body["code"] != 200


# ═══════════════════════════════════════════════════════════════════════
# 文件删除
# ═══════════════════════════════════════════════════════════════════════

class TestFileDeleteAPI:
    def test_delete_file(self, client, admin_headers, db, admin_user):
        file_obj = File(
            name="del_target.jpg", path="uploads/test/del_target.jpg",
            size=256, mime_type="image/jpeg", file_type="image",
            extension="jpg", uploader_id=admin_user.id,
        )
        db.add(file_obj)
        db.commit()
        db.refresh(file_obj)

        # 创建磁盘文件
        abs_path = os.path.join(settings.STATIC_PATH, file_obj.path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write("test")

        resp = client.post("/api/v1/resource/file/delete", headers=admin_headers, json=[str(file_obj.id)])
        body = resp.json()
        assert body["code"] == 200

        # 清理
        if os.path.exists(abs_path):
            os.remove(abs_path)

    def test_delete_nonexistent_file(self, client, admin_headers, db):
        from uuid import uuid4
        resp = client.post("/api/v1/resource/file/delete", headers=admin_headers, json=[str(uuid4())])
        body = resp.json()
        assert body["code"] == 200


# ═══════════════════════════════════════════════════════════════════════
# 文件预览
# ═══════════════════════════════════════════════════════════════════════

class TestFilePreviewAPI:
    def test_preview_nonexistent_file(self, client, admin_headers, db, admin_user):
        from uuid import uuid4
        resp = client.get(f"/api/v1/resource/file/preview/{uuid4()}", headers=admin_headers)
        body = resp.json()
        assert body["code"] != 200

    def test_preview_file_missing_on_disk(self, client, admin_headers, db, admin_user):
        """DB 有记录但磁盘文件丢失"""
        file_obj = File(
            name="missing.jpg", path="uploads/test/missing.jpg",
            size=100, mime_type="image/jpeg", file_type="image",
            extension="jpg", uploader_id=admin_user.id,
        )
        db.add(file_obj)
        db.commit()
        db.refresh(file_obj)

        resp = client.get(f"/api/v1/resource/file/preview/{file_obj.id}", headers=admin_headers)
        body = resp.json()
        assert body["code"] != 200  # 文件已丢失


# ═══════════════════════════════════════════════════════════════════════
# 签名 URL
# ═══════════════════════════════════════════════════════════════════════

class TestFileSignURLAPI:
    def test_get_sign_url(self, client, admin_headers, db, admin_user):
        file_obj = File(
            name="sign_test.jpg", path="uploads/test/sign.jpg",
            size=100, mime_type="image/jpeg", file_type="image",
            extension="jpg", uploader_id=admin_user.id,
        )
        db.add(file_obj)
        db.commit()
        db.refresh(file_obj)

        resp = client.get(f"/api/v1/resource/file/sign-url/{file_obj.id}", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert "url" in body["data"]
        assert "sign=" in body["data"]["url"]

    def test_get_sign_url_nonexistent(self, client, admin_headers, db, admin_user):
        from uuid import uuid4
        resp = client.get(f"/api/v1/resource/file/sign-url/{uuid4()}", headers=admin_headers)
        body = resp.json()
        assert body["code"] != 200


# ═══════════════════════════════════════════════════════════════════════
# 存储统计
# ═══════════════════════════════════════════════════════════════════════

class TestFileStatsAPI:
    def test_get_storage_stats(self, client, admin_headers, db, admin_user):
        file_obj = File(
            name="stats_test.jpg", path="uploads/test/stats.jpg",
            size=2048, mime_type="image/jpeg", file_type="image",
            extension="jpg", uploader_id=admin_user.id,
        )
        db.add(file_obj)
        db.commit()

        resp = client.get("/api/v1/resource/file/stats", headers=admin_headers)
        body = resp.json()
        assert body["code"] == 200
        assert "total_files" in body["data"]
        assert "total_size" in body["data"]
        assert "type_stats" in body["data"]
        assert "total_size_display" in body["data"]
