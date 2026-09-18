"""utils/__init__.py 中未被覆盖工具函数的单元测试"""

import binascii
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest

from app.settings import settings
from app.utils import (
    base_decode,
    generate_password_reset_token,
    generate_uuid,
    menuTree,
    now,
    random_string,
    verify_password_reset_token,
)


class TestPasswordResetToken:
    def test_generate_and_verify_roundtrip(self):
        token = generate_password_reset_token("a@b.com")
        assert verify_password_reset_token(token) == "a@b.com"

    def test_verify_invalid_token(self):
        assert verify_password_reset_token("not-a-token") is None

    def test_generate_token_payload(self):
        token = generate_password_reset_token("x@y.com")
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert decoded["sub"] == "x@y.com"
        assert "exp" in decoded
        assert "nbf" in decoded


class TestBaseDecode:
    def test_decode_normal(self):
        assert base_decode("YWJj") == b"abc"

    def test_decode_still_needs_padding(self):
        # 长度 %3 == 2 分支会补一个 "="，但 base64 需要按 4 取模补位
        with pytest.raises(binascii.Error):
            base_decode("YWI")

    def test_decode_two_padding_branch(self):
        # 长度 %3 == 1 分支会补两个 "="
        with pytest.raises(binascii.Error):
            base_decode("YQ")


class TestGenerateUuid:
    def test_returns_uuid5(self):
        result = generate_uuid("name")
        assert isinstance(result, uuid.UUID)
        assert result.version == 5

    def test_unique_with_time(self):
        assert generate_uuid("same") != generate_uuid("same")


class TestNow:
    def test_variant_zero_datetime(self):
        assert isinstance(now(0), datetime)

    def test_variant_one_str(self):
        value = now(1)
        assert isinstance(value, str)
        assert len(value) == 19

    def test_variant_two_timestamp(self):
        assert isinstance(now(2), float)

    def test_variant_three_compact(self):
        value = now(3)
        assert isinstance(value, str)
        assert len(value) == 14

    def test_default_variant(self):
        assert len(now(99)) == 19

    def test_no_arg(self):
        assert isinstance(now(), str)


class TestRandomString:
    def test_without_prefix(self):
        value = random_string(5)
        assert value.startswith("-")
        assert len(value) == 6

    def test_with_prefix(self):
        value = random_string(4, prefix="abc")
        assert value.startswith("abc-")
        assert len(value) == 8


def _make_menu(**kwargs):
    menu = MagicMock()
    menu.parentId = kwargs.get("parentId", "1")
    menu.rank = kwargs.get("rank", 1)
    data = {
        "id": kwargs.get("id", "2"),
        "title": "t",
        "icon": "i",
        "extraIcon": "",
        "showLink": True,
        "showParent": False,
        "auths": [],
        "keepAlive": False,
        "frameSrc": "",
        "frameLoading": False,
        "hiddenTag": False,
        "dynamicLevel": 0,
        "activePath": "",
        "transitionName": "fade",
        "enterTransition": "",
        "leaveTransition": "",
        "rank": kwargs.get("rank", 1),
    }
    menu.to_dict = AsyncMock(return_value=dict(data))
    return menu


class TestMenuTree:
    @pytest.mark.asyncio
    async def test_no_children_removes_key(self):
        parent = {"id": "1", "children": []}
        result = await menuTree(parent, [])
        assert "children" not in result

    @pytest.mark.asyncio
    async def test_with_children_sorted_and_recursed(self):
        parent = {"id": "1", "children": []}
        child_a = _make_menu(id="2", parentId="1", rank=2)
        child_b = _make_menu(id="3", parentId="1", rank=1)
        result = await menuTree(parent, [child_a, child_b])
        assert [c["id"] for c in result["children"]] == ["3", "2"]
        # 叶子节点 children 被删除
        assert "children" not in result["children"][0]
        assert result["children"][0]["meta"]["title"] == "t"

    @pytest.mark.asyncio
    async def test_ignores_unrelated_menu(self):
        parent = {"id": "1", "children": []}
        other = _make_menu(id="9", parentId="8")
        result = await menuTree(parent, [other])
        assert "children" not in result
