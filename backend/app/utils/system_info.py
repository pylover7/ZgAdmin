import os
from collections import namedtuple

import psutil


def _fmt_bytes(b: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}PB"


def _fmt_rate(b: float) -> str:
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB/s"


def _fmt_freq(mhz: float) -> str:
    if mhz >= 1000:
        return f"{mhz / 1000:.2f}GHz"
    return f"{mhz:.0f}MHz"


def _load_status(load1: float, cores: int) -> str:
    ratio = load1 / cores if cores else 0
    if ratio < 0.7:
        return "正常"
    if ratio < 1.0:
        return "偏高"
    return "过载"


LoadInfo = namedtuple("LoadInfo", ["load1", "load5", "load15", "status", "cores", "percent"])
CpuInfo = namedtuple("CpuInfo", ["percent", "freq", "per_cpu", "physical_cores", "logical_cores"])
MemoryInfo = namedtuple(
    "MemoryInfo",
    ["percent", "total", "used", "available", "cached", "buffers", "shared"],
)
DiskInfo = namedtuple("DiskInfo", ["percent", "total", "used", "free", "read_speed", "write_speed"])
ProcessItem = namedtuple("ProcessItem", ["pid", "name", "cpu_percent", "memory_percent"])


def _get_host_cpu_count() -> int:
    """获取宿主机的真实 CPU 核心数。

    Docker 容器中 os.getloadavg() 返回的是宿主机的负载均值，
    但 os.cpu_count() 可能只返回容器限制的 CPU 数，
    导致负载百分比计算失真。通过多个来源取最大值，最大限度避免低估。
    """
    counts: list[int] = []

    # 来源 1: /proc/cpuinfo（cgroup v2 下可能被截断）
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            count = sum(1 for line in f if line.startswith("processor"))
            if count > 0:
                counts.append(count)
    except (FileNotFoundError, OSError):
        pass

    # 来源 2: /sys/devices/system/cpu/present（通常不被命名空间化）
    try:
        with open("/sys/devices/system/cpu/present", encoding="utf-8") as f:
            content = f.read().strip()
            max_id = 0
            for part in content.split(","):
                p = part.strip()
                if "-" in p:
                    max_id = max(max_id, int(p.split("-")[1]))
                elif p.isdigit():
                    max_id = max(max_id, int(p))
            counts.append(max_id + 1)
    except (FileNotFoundError, OSError, ValueError):
        pass

    # 来源 3: os.cpu_count()
    count = os.cpu_count()
    if count:
        counts.append(count)

    return max(counts) if counts else 1


def _is_container_cpu_limited() -> bool:
    """检测是否在具有 CPU 限制的容器中运行。

    当容器有 cgroup CPU 配额时，os.getloadavg() 仍返回宿主机负载，
    但可见 CPU 数量可能只是容器配额，导致 load1/cores 失真。
    """
    # cgroup v2
    try:
        with open("/sys/fs/cgroup/cpu.max", encoding="utf-8") as f:
            parts = f.read().strip().split()
            if parts and parts[0] != "max":
                return True
    except (FileNotFoundError, OSError, IndexError):
        pass

    # cgroup v1
    try:
        with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us", encoding="utf-8") as f:
            quota = int(f.read().strip())
            if quota > 0:
                return True
    except (FileNotFoundError, OSError, ValueError):
        pass

    return False


def get_load_info(cpu_percent: float | None = None) -> LoadInfo:
    cores = _get_host_cpu_count()
    try:
        load1, load5, load15 = os.getloadavg()
    except OSError:
        load1 = load5 = load15 = 0.0

    # 容器有 CPU 限制时，os.getloadavg() 返回宿主机负载，
    # load1/cores 不再可靠，改用 psutil.cpu_percent()（容器感知）
    if _is_container_cpu_limited() and cpu_percent is not None:
        percent = round(cpu_percent, 1)
    else:
        percent = min(round(load1 / cores * 100, 1), 100) if cores else 0

    status = _load_status(load1, cores)
    return LoadInfo(
        load1=round(load1, 2),
        load5=round(load5, 2),
        load15=round(load15, 2),
        status=status,
        cores=cores,
        percent=percent,
    )


def get_cpu_info() -> CpuInfo:
    percent = psutil.cpu_percent(interval=0)
    freq = psutil.cpu_freq()
    freq_str = _fmt_freq(freq.current) if freq else "N/A"
    per_cpu = psutil.cpu_percent(interval=0, percpu=True)
    physical = psutil.cpu_count(logical=False) or 0
    logical = psutil.cpu_count(logical=True) or 0
    return CpuInfo(
        percent=percent,
        freq=freq_str,
        per_cpu=per_cpu,
        physical_cores=physical,
        logical_cores=logical,
    )


def get_memory_info() -> MemoryInfo:
    mem = psutil.virtual_memory()
    cached = getattr(mem, "cached", 0) or 0
    buffers = getattr(mem, "buffers", 0) or 0
    shared = getattr(mem, "shared", 0) or 0
    return MemoryInfo(
        percent=mem.percent,
        total=_fmt_bytes(mem.total),
        used=_fmt_bytes(mem.used),
        available=_fmt_bytes(mem.available),
        cached=_fmt_bytes(cached),
        buffers=_fmt_bytes(buffers),
        shared=_fmt_bytes(shared),
    )


def get_disk_info() -> DiskInfo:
    disk = psutil.disk_usage("/")
    return DiskInfo(
        percent=disk.percent,
        total=_fmt_bytes(disk.total),
        used=_fmt_bytes(disk.used),
        free=_fmt_bytes(disk.free),
        read_speed="0B/s",
        write_speed="0B/s",
    )


def get_network_io():
    counters = psutil.net_io_counters(pernic=True)
    result = {}
    for name, c in counters.items():
        if name == "lo":
            continue
        result[name] = {
            "bytes_sent": c.bytes_sent,
            "bytes_recv": c.bytes_recv,
            "packets_sent": c.packets_sent,
            "packets_recv": c.packets_recv,
        }
    return result


def get_disk_io():
    try:
        counters = psutil.disk_io_counters(perdisk=True)
    except Exception:
        return {}
    if not counters:
        return {}
    result = {}
    for name, c in counters.items():
        if name.startswith(("loop", "dm-")):
            continue
        result[name] = {
            "read_bytes": c.read_bytes,
            "write_bytes": c.write_bytes,
            "read_count": c.read_count,
            "write_count": c.write_count,
        }
    return result


def get_top_processes(n: int = 5) -> list[ProcessItem]:
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append(
                ProcessItem(
                    pid=info["pid"],
                    name=info["name"] or "",
                    cpu_percent=info["cpu_percent"] or 0,
                    memory_percent=round(info["memory_percent"] or 0, 1),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x.cpu_percent, reverse=True)
    return procs[:n]
