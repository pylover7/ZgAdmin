"""utils/ip.py、utils/staticFileUtils.py、settings/database.py 单元测试"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.settings.database import db_engine
from app.utils.ip import SysBro, getIpAddress, getReqSysBro
from app.utils.staticFileUtils import check_dir_exists


class TestGetIpAddress:
    @pytest.mark.asyncio
    async def test_private_ip_short_circuit(self):
        assert await getIpAddress("192.168.1.1") == "内网IP"

    @pytest.mark.asyncio
    async def test_api2_success(self):
        resp = MagicMock()
        resp.json.return_value = {"data": {"address": " 中国 北京 "}}
        client = AsyncMock()
        client.__aenter__.return_value.get = AsyncMock(return_value=resp)
        client.__aexit__ = AsyncMock(return_value=False)
        with patch("app.utils.ip.httpx.AsyncClient", return_value=client):
            assert await getIpAddress("8.8.8.8") == "中国北京"

    @pytest.mark.asyncio
    async def test_api2_fail_api1_success(self):
        bad = MagicMock()
        bad.json.side_effect = KeyError("data")
        good = MagicMock()
        good.json.return_value = {"data": [{"location": " 美国 加利福尼亚 "}]}
        client = AsyncMock()
        client.__aenter__.return_value.get = AsyncMock(side_effect=[bad, good])
        client.__aexit__ = AsyncMock(return_value=False)
        with patch("app.utils.ip.httpx.AsyncClient", return_value=client):
            assert await getIpAddress("8.8.4.4") == "美国加利福尼亚"

    @pytest.mark.asyncio
    async def test_both_apis_fail(self):
        bad = MagicMock()
        bad.json.side_effect = KeyError("nope")
        client = AsyncMock()
        client.__aenter__.return_value.get = AsyncMock(side_effect=[bad, bad])
        client.__aexit__ = AsyncMock(return_value=False)
        with patch("app.utils.ip.httpx.AsyncClient", return_value=client):
            assert await getIpAddress("1.1.1.1") == ""


class TestGetReqSysBro:
    @pytest.mark.asyncio
    async def test_parses_ua(self):
        req = MagicMock()
        req.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
        result = await getReqSysBro(req)
        assert isinstance(result, SysBro)
        assert result.system == "Windows NT 10.0"
        assert result.browser == "Chrome"

    @pytest.mark.asyncio
    async def test_no_ua(self):
        req = MagicMock()
        req.headers = {}
        result = await getReqSysBro(req)
        assert result.system == "未知系统"
        assert result.browser == "未知浏览器"

    @pytest.mark.asyncio
    async def test_ua_no_match(self):
        req = MagicMock()
        req.headers = {"User-Agent": "curl/8.0"}
        result = await getReqSysBro(req)
        assert result.system == "未知系统"
        assert result.browser == "未知浏览器"


class TestCheckDirExists:
    def test_creates_dirs(self, tmp_path):
        target = tmp_path / "a" / "b"
        check_dir_exists([str(target)])
        assert target.is_dir()

    def test_existing_dir_ok(self, tmp_path):
        check_dir_exists([str(tmp_path)])
        assert tmp_path.is_dir()


class TestDbEngine:
    def test_postgresql(self):
        url = db_engine("postgresql", "u", "p", "h", 5432, "/db")
        assert "postgresql+psycopg" in url

    def test_mysql(self):
        url = db_engine("mysql", "u", "p", "h", 3306, "/db")
        assert "mysql+pymysql" in url

    def test_default_sqlite(self):
        url = db_engine("sqlite")
        assert url.startswith("sqlite:////") and "zgadmin.sqlite" in url

    def test_sqlite_path_points_to_static(self):
        url = db_engine()
        assert Path("static/zgadmin.sqlite").name in url
