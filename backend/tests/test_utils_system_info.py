"""utils/system_info.py 单元测试"""

from unittest.mock import MagicMock, patch

from app.utils import system_info as si


class TestFormatters:
    def test_fmt_bytes_units(self):
        assert si._fmt_bytes(0) == "0.0B"
        assert si._fmt_bytes(512) == "512.0B"
        assert si._fmt_bytes(2048) == "2.0KB"
        assert si._fmt_bytes(1024**3) == "1.0GB"
        assert si._fmt_bytes(1024**5) == "1.0PB"

    def test_fmt_rate_units(self):
        assert si._fmt_rate(100) == "100.0B/s"
        assert si._fmt_rate(1024) == "1.0KB/s"
        assert si._fmt_rate(1024**4) == "1.0TB/s"

    def test_fmt_freq(self):
        assert si._fmt_freq(500) == "500MHz"
        assert si._fmt_freq(2400) == "2.40GHz"

    def test_load_status(self):
        assert si._load_status(0.1, 4) == "正常"
        assert si._load_status(3.0, 4) == "偏高"
        assert si._load_status(10.0, 4) == "过载"

    def test_load_status_zero_cores(self):
        assert si._load_status(1.0, 0) == "正常"


class TestHostCpuCount:
    def test_reads_proc_cpuinfo(self):
        proc = ["processor\t: 0\n", "processor\t: 1\n", "model name\n"]

        def fake_open(path, *a, **kw):
            m = MagicMock()
            if "cpuinfo" in str(path):
                m.__enter__.return_value = proc
            else:
                m.__enter__.return_value.read.return_value = "0-3"
            return m

        with patch("builtins.open", side_effect=fake_open), patch.object(si.os, "cpu_count", return_value=1):
            count = si._get_host_cpu_count()
        assert count == 4

    def test_fallback_cpu_count(self):
        with patch("builtins.open", side_effect=FileNotFoundError), patch.object(si.os, "cpu_count", return_value=3):
            assert si._get_host_cpu_count() == 3

    def test_minimum_one(self):
        with patch("builtins.open", side_effect=FileNotFoundError), patch.object(si.os, "cpu_count", return_value=None):
            assert si._get_host_cpu_count() == 1

    def test_sys_present_range(self):
        content = "0-3,5"

        def fake_open(path, *a, **kw):
            m = MagicMock()
            if "cpuinfo" in str(path):
                m.__enter__.return_value = []
            else:
                m.__enter__.return_value.read.return_value = content
            return m

        with patch("builtins.open", side_effect=fake_open), patch.object(si.os, "cpu_count", return_value=1):
            assert si._get_host_cpu_count() == 6


class TestContainerLimited:
    def test_cgroup_v2_limit(self):
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "50000 100000"
        with patch("builtins.open", return_value=mock_file):
            assert si._is_container_cpu_limited() is True

    def test_cgroup_v2_max(self):
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "max 100000"
        with patch("builtins.open", return_value=mock_file):
            assert si._is_container_cpu_limited() is False

    def test_cgroup_v1_quota(self):
        calls = {"n": 0}

        def fake_open(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise FileNotFoundError
            m = MagicMock()
            m.__enter__.return_value.read.return_value = "20000"
            return m

        with patch("builtins.open", side_effect=fake_open):
            assert si._is_container_cpu_limited() is True

    def test_no_limit(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            assert si._is_container_cpu_limited() is False

    def test_cgroup_v1_invalid(self):
        calls = {"n": 0}

        def fake_open(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise FileNotFoundError
            m = MagicMock()
            m.__enter__.return_value.read.return_value = "abc"
            return m

        with patch("builtins.open", side_effect=fake_open):
            assert si._is_container_cpu_limited() is False


class TestInfoCollectors:
    def test_get_load_info_normal(self):
        with (
            patch.object(si, "_get_host_cpu_count", return_value=4),
            patch.object(si, "_is_container_cpu_limited", return_value=False),
            patch.object(si.os, "getloadavg", return_value=(1.0, 0.5, 0.2)),
        ):
            info = si.get_load_info()
        assert info.cores == 4
        assert info.load1 == 1.0
        assert info.percent == 25.0

    def test_get_load_info_container_limited(self):
        with (
            patch.object(si, "_get_host_cpu_count", return_value=4),
            patch.object(si, "_is_container_cpu_limited", return_value=True),
            patch.object(si.os, "getloadavg", return_value=(1.0, 0.5, 0.2)),
        ):
            info = si.get_load_info(cpu_percent=42.5)
        assert info.percent == 42.5

    def test_get_load_info_no_loadavg(self):
        with (
            patch.object(si, "_get_host_cpu_count", return_value=4),
            patch.object(si, "_is_container_cpu_limited", return_value=False),
            patch.object(si.os, "getloadavg", side_effect=OSError),
        ):
            info = si.get_load_info()
        assert info.load1 == 0.0

    def test_get_cpu_info(self):
        with (
            patch.object(si.psutil, "cpu_percent", return_value=10.0),
            patch.object(si.psutil, "cpu_freq", return_value=None),
            patch.object(si.psutil, "cpu_count", return_value=8),
        ):
            info = si.get_cpu_info()
        assert info.freq == "N/A"
        assert info.logical_cores == 8

    def test_get_cpu_info_with_freq(self):
        freq = MagicMock()
        freq.current = 2400.0
        with (
            patch.object(si.psutil, "cpu_percent", return_value=10.0),
            patch.object(si.psutil, "cpu_freq", return_value=freq),
            patch.object(si.psutil, "cpu_count", return_value=8),
        ):
            info = si.get_cpu_info()
        assert info.freq == "2.40GHz"

    def test_get_memory_info(self):
        mem = MagicMock()
        mem.percent = 50.0
        mem.total = 1024**3
        mem.used = 1024**2
        mem.available = 512 * 1024**2
        mem.cached = 1024**2
        mem.buffers = 1024**2
        mem.shared = 1024**2
        with patch.object(si.psutil, "virtual_memory", return_value=mem):
            info = si.get_memory_info()
        assert info.total == "1.0GB"

    def test_get_disk_info(self):
        disk = MagicMock()
        disk.percent = 30.0
        disk.total = 1024**3
        disk.used = 1024**2
        disk.free = 1024**2
        with patch.object(si.psutil, "disk_usage", return_value=disk):
            info = si.get_disk_info()
        assert info.read_speed == "0B/s"
        assert info.percent == 30.0

    def test_get_network_io_skips_lo(self):
        c = MagicMock(bytes_sent=1, bytes_recv=2, packets_sent=3, packets_recv=4)
        with patch.object(si.psutil, "net_io_counters", return_value={"lo": c, "eth0": c}):
            result = si.get_network_io()
        assert set(result.keys()) == {"eth0"}

    def test_get_disk_io(self):
        c = MagicMock(read_bytes=1, write_bytes=2, read_count=3, write_count=4)
        with patch.object(si.psutil, "disk_io_counters", return_value={"sda": c, "loop0": c, "dm-0": c}):
            result = si.get_disk_io()
        assert set(result.keys()) == {"sda"}

    def test_get_disk_io_empty(self):
        with patch.object(si.psutil, "disk_io_counters", return_value=None):
            assert si.get_disk_io() == {}

    def test_get_disk_io_exception(self):
        with patch.object(si.psutil, "disk_io_counters", side_effect=RuntimeError):
            assert si.get_disk_io() == {}

    def test_get_top_processes(self):
        p1 = MagicMock()
        p1.info = {"pid": 1, "name": "a", "cpu_percent": 5.0, "memory_percent": 1.234}
        p2 = MagicMock()
        p2.info = {"pid": 2, "name": "b", "cpu_percent": 9.0, "memory_percent": 0.5}
        with patch.object(si.psutil, "process_iter", return_value=[p1, p2]):
            result = si.get_top_processes(1)
        assert len(result) == 1
        assert result[0].pid == 2

    def test_get_top_processes_skips_missing(self):
        bad = MagicMock()
        type(bad).info = property(lambda self: (_ for _ in ()).throw(si.psutil.NoSuchProcess(1)))
        with patch.object(si.psutil, "process_iter", return_value=[bad]):
            assert si.get_top_processes() == []
