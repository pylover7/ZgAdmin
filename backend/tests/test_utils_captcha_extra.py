"""captcha 字体回退与 seeder 深层递归、CRUD 无 id 模型边界测试"""

from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


class TestCaptchaFontFallback:
    def test_all_fonts_missing_uses_default(self):
        from PIL import ImageFont

        from app.utils.captcha import _create_captcha_image

        real_default = ImageFont.load_default(size=12)
        with (
            patch("app.utils.captcha.ImageFont.truetype", side_effect=OSError("no font")),
            patch("app.utils.captcha.ImageFont.load_default", return_value=real_default) as mock_default,
        ):
            data = _create_captcha_image("AB12")
            mock_default.assert_called_once()
        assert isinstance(data, bytes)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"


class TestSeederRecursion:
    def test_deeply_nested_menu_tree(self):
        from app.models import Department, Menu
        from app.seed import seeder

        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(engine)

        nested = [
            {
                "menuType": 0,
                "title": "L1",
                "name": "L1",
                "path": "/l1",
                "component": "",
                "rank": 1,
                "children": [
                    {
                        "menuType": 0,
                        "title": "L2",
                        "name": "L2",
                        "path": "/l2",
                        "component": "",
                        "rank": 1,
                        "children": [
                            {
                                "menuType": 0,
                                "title": "L3",
                                "name": "L3",
                                "path": "/l3",
                                "component": "",
                                "rank": 1,
                            }
                        ],
                    }
                ],
            }
        ]
        with (
            patch.object(seeder, "DEFAULT_MENUS", nested),
            patch.object(seeder, "DEFAULT_DEPARTMENTS", [{"name": "总部", "sort": 0, "status": 0}]),
            Session(engine) as session,
        ):
            seeder.seed_menus(session)
            menus = session.exec(__import__("sqlmodel").select(Menu)).all()
            assert len(menus) == 3
            Depts = session.exec(__import__("sqlmodel").select(Department)).all()
            assert Depts == []


class TestCrudModelWithoutId:
    @pytest.mark.asyncio
    async def test_list_raises_without_id(self):
        from app.core.crud import CRUDBase

        class NoId:
            """无 id 属性的伪模型"""

        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        crud = CRUDBase(NoId)
        with Session(engine) as session, pytest.raises(AttributeError, match="does not have an 'id'"):
            await crud.list(session)
