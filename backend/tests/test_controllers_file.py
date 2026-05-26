"""controllers/file.py 单元测试 — 文件上传/删除/统计"""
import os
import pytest
import tempfile
from uuid import uuid4

from sqlmodel import Session, SQLModel, create_engine

from app.controllers.file import fileController
from app.models.file import File
from app.settings import settings


# ─── 独立内存 DB ─────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def file_engine():
    _engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture
def file_session(file_engine):
    from sqlalchemy import event
    connection = file_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ═══════════════════════════════════════════════════════════════════════
# create_from_upload
# ═══════════════════════════════════════════════════════════════════════

class TestFileCreateFromUpload:
    @pytest.mark.asyncio
    async def test_upload_valid_image(self, file_session):
        # 创建最小 PNG 文件内容
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        result = await fileController.create_from_upload(
            session=file_session,
            filename="test.png",
            file_content=png_content,
            uploader_id=uuid4(),
        )
        assert not isinstance(result, tuple), f"Upload failed: {result[1]}"
        assert result.name == "test.png"
        assert result.extension == "png"
        assert result.size > 0

        # 清理磁盘文件
        abs_path = os.path.join(settings.STATIC_PATH, result.path)
        if os.path.exists(abs_path):
            os.remove(abs_path)

    @pytest.mark.asyncio
    async def test_upload_invalid_extension(self, file_session):
        result = await fileController.create_from_upload(
            session=file_session,
            filename="virus.exe",
            file_content=b"malware",
            uploader_id=uuid4(),
        )
        assert isinstance(result, tuple)
        assert result[0] is None
        assert "不允许" in result[1]

    @pytest.mark.asyncio
    async def test_upload_oversized_file(self, file_session):
        # 临时修改 MAX_UPLOAD_SIZE
        from unittest.mock import patch
        with patch.object(settings, "MAX_UPLOAD_SIZE", 10):  # 10 bytes
            result = await fileController.create_from_upload(
                session=file_session,
                filename="big.jpg",
                file_content=b"x" * 100,
                uploader_id=uuid4(),
            )
        assert isinstance(result, tuple)
        assert result[0] is None
        assert "超过限制" in result[1]


# ═══════════════════════════════════════════════════════════════════════
# delete_files
# ═══════════════════════════════════════════════════════════════════════

class TestFileDelete:
    @pytest.mark.asyncio
    async def test_delete_existing_file(self, file_session):
        # 先上传
        file_obj = File(
            name="del.jpg", path="uploads/test/del.jpg", size=100,
            mime_type="image/jpeg", file_type="image", extension="jpg",
            uploader_id=uuid4(),
        )
        file_session.add(file_obj)
        file_session.commit()
        file_session.refresh(file_obj)

        # 创建磁盘文件
        abs_path = os.path.join(settings.STATIC_PATH, file_obj.path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write("test")

        success, failed = await fileController.delete_files(file_session, [file_obj.id])
        assert success == 1
        assert failed == 0

        # 清理
        if os.path.exists(abs_path):
            os.remove(abs_path)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, file_session):
        success, failed = await fileController.delete_files(file_session, [uuid4()])
        assert success == 0
        assert failed == 1


# ═══════════════════════════════════════════════════════════════════════
# get_storage_stats
# ═══════════════════════════════════════════════════════════════════════

class TestFileStats:
    @pytest.mark.asyncio
    async def test_storage_stats(self, file_session):
        file_obj = File(
            name="stat.jpg", path="uploads/test/stat.jpg", size=500,
            mime_type="image/jpeg", file_type="image", extension="jpg",
            uploader_id=uuid4(),
        )
        file_session.add(file_obj)
        file_session.commit()

        stats = await fileController.get_storage_stats(file_session)
        assert "total_files" in stats
        assert "total_size" in stats
        assert "type_stats" in stats
        assert stats["total_files"] >= 1
