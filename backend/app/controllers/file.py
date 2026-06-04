import os
from uuid import UUID

from sqlmodel import Session, func, select

from app.core.crud import CRUDBase
from app.models.file import File, FileCreate, FileUpdate
from app.settings import settings
from app.settings.log import logger
from app.utils.file_upload import (
    classify_file,
    detect_mime,
    ensure_storage_dir,
    generate_storage_path,
    validate_extension,
    validate_mime_extension,
)


class FileController(CRUDBase[File, FileCreate, FileUpdate]):
    def __init__(self):
        super().__init__(File)

    async def create_from_upload(
        self,
        session: Session,
        filename: str,
        file_content: bytes,
        uploader_id: UUID,
    ) -> File | tuple[None, str]:
        """处理单个文件上传：校验 → 存储 → 检测 MIME → 创建记录"""
        # 1. 校验扩展名
        ext, err = validate_extension(filename)
        if err:
            return None, err

        # 2. 校验文件大小
        max_size = settings.MAX_UPLOAD_SIZE
        if len(file_content) > max_size:
            return None, f"文件大小超过限制({max_size // (1024 * 1024)}MB)"

        # 3. 生成存储路径并写入磁盘
        storage_path = generate_storage_path(ext)
        abs_path = ensure_storage_dir(storage_path)
        with open(abs_path, "wb") as f:
            f.write(file_content)

        # 4. 检测真实 MIME 类型
        mime_type = detect_mime(abs_path)

        # 5. 校验 MIME 与扩展名一致性
        mime_valid, mime_err = validate_mime_extension(mime_type, ext)
        if not mime_valid:
            # MIME 与扩展名不匹配 → 删除已写入的文件并拒绝
            os.remove(abs_path)
            return None, mime_err

        # 6. 分类
        file_type = classify_file(mime_type, ext)

        # 7. 创建数据库记录
        file_obj = File(
            name=filename,
            path=storage_path,
            size=len(file_content),
            mime_type=mime_type,
            file_type=file_type,
            extension=ext,
            uploader_id=uploader_id,
        )
        session.add(file_obj)
        session.commit()
        session.refresh(file_obj)
        logger.info(f"文件上传成功: {filename} -> {storage_path}")
        return file_obj

    async def delete_files(self, session: Session, ids: list[UUID]) -> tuple[int, int]:
        """删除文件记录和磁盘文件，返回 (成功数, 失败数)"""
        success = 0
        failed = 0
        for file_id in ids:
            file_obj = session.get(self.model, file_id)
            if not file_obj:
                failed += 1
                continue
            # 删除磁盘文件
            abs_path = f"{settings.STATIC_PATH}/{file_obj.path}"
            if os.path.exists(abs_path):
                os.remove(abs_path)
            session.delete(file_obj)
            success += 1
        session.commit()
        return success, failed

    async def get_storage_stats(self, session: Session) -> dict:
        """获取存储统计信息"""
        total_files = session.exec(select(func.count()).select_from(File)).one()
        total_size = session.exec(select(func.coalesce(func.sum(File.size), 0)).select_from(File)).one()
        # 按类型统计
        type_stats = []
        type_stmt = select(
            File.file_type,
            func.count(File.id).label("count"),
            func.coalesce(func.sum(File.size), 0).label("size"),
        ).group_by(File.file_type)
        for row in session.exec(type_stmt):
            type_stats.append(
                {
                    "file_type": row[0],
                    "count": row[1],
                    "size": row[2],
                }
            )
        return {
            "total_files": total_files,
            "total_size": total_size,
            "type_stats": type_stats,
        }


fileController = FileController()
