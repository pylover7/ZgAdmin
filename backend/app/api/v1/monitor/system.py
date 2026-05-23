import time
from collections import deque

import psutil
from fastapi import APIRouter, Query

from app.models import Success
from app.utils.system_info import (
    get_load_info, get_cpu_info, get_memory_info, get_disk_info,
    get_network_io, get_disk_io, get_top_processes, _fmt_rate,
)

systemMonitorRouter = APIRouter()

# ─── 网络流量速率计算 ───
_prev_net: dict = {}
_prev_net_time: float = 0
_net_history: dict[str, deque] = {}

# ─── 磁盘IO速率计算 ───
_prev_disk: dict = {}
_prev_disk_time: float = 0
_disk_io_history: dict[str, deque] = {}

HISTORY_MAX = 1200


@systemMonitorRouter.get("/status")
async def system_status():
    cpu_pct = psutil.cpu_percent(interval=0)
    load = get_load_info(cpu_percent=cpu_pct)
    cpu = get_cpu_info()
    mem = get_memory_info()
    disk = get_disk_info()
    top_cpu = get_top_processes(5)
    return Success(data={
        "load": {
            "load1": load.load1, "load5": load.load5, "load15": load.load15,
            "status": load.status, "cores": load.cores, "percent": load.percent,
        },
        "cpu": {
            "percent": cpu.percent, "freq": cpu.freq,
            "per_cpu": cpu.per_cpu,
            "physical_cores": cpu.physical_cores,
            "logical_cores": cpu.logical_cores,
        },
        "memory": {
            "percent": mem.percent, "total": mem.total,
            "used": mem.used, "available": mem.available,
            "cached": mem.cached, "buffers": mem.buffers, "shared": mem.shared,
        },
        "disk": {
            "percent": disk.percent, "total": disk.total,
            "used": disk.used, "free": disk.free,
        },
        "top_cpu": [
            {"pid": p.pid, "name": p.name,
             "cpu_percent": p.cpu_percent, "memory_percent": p.memory_percent}
            for p in top_cpu
        ],
    })


@systemMonitorRouter.get("/network")
async def network_monitor(iface: str = Query(default="")):
    global _prev_net, _prev_net_time  # pylint: disable=global-statement
    current = get_network_io()
    now = time.time()

    result: dict = {}
    for name, counters in current.items():
        if iface and name != iface:
            continue
        sent_speed = 0.0
        recv_speed = 0.0
        if name in _prev_net and _prev_net_time > 0:
            dt = now - _prev_net_time
            if dt > 0:
                sent_speed = (counters["bytes_sent"] - _prev_net[name]["bytes_sent"]) / dt
                recv_speed = (counters["bytes_recv"] - _prev_net[name]["bytes_recv"]) / dt

        if name not in _net_history:
            _net_history[name] = deque(maxlen=HISTORY_MAX)
        _net_history[name].append({
            "time": round(now * 1000),
            "sent_speed": round(sent_speed, 1),
            "recv_speed": round(recv_speed, 1),
        })
        result[name] = {
            "bytes_sent": counters["bytes_sent"],
            "bytes_recv": counters["bytes_recv"],
            "sent_speed": _fmt_rate(sent_speed),
            "recv_speed": _fmt_rate(recv_speed),
            "sent_speed_raw": round(sent_speed, 1),
            "recv_speed_raw": round(recv_speed, 1),
            "history": list(_net_history[name]),
        }

    _prev_net = current
    _prev_net_time = now

    if iface:
        return Success(data=result.get(iface, {}))
    return Success(data=result)


@systemMonitorRouter.get("/disk-io")
async def disk_io_monitor():
    global _prev_disk, _prev_disk_time  # pylint: disable=global-statement
    current = get_disk_io()
    now = time.time()

    result: dict = {}
    for name, counters in current.items():
        read_speed = 0.0
        write_speed = 0.0
        if name in _prev_disk and _prev_disk_time > 0:
            dt = now - _prev_disk_time
            if dt > 0:
                read_speed = (counters["read_bytes"] - _prev_disk[name]["read_bytes"]) / dt
                write_speed = (counters["write_bytes"] - _prev_disk[name]["write_bytes"]) / dt

        if name not in _disk_io_history:
            _disk_io_history[name] = deque(maxlen=HISTORY_MAX)
        _disk_io_history[name].append({
            "time": round(now * 1000),
            "read_speed": round(read_speed, 1),
            "write_speed": round(write_speed, 1),
        })
        result[name] = {
            "read_bytes": counters["read_bytes"],
            "write_bytes": counters["write_bytes"],
            "read_speed": _fmt_rate(read_speed),
            "write_speed": _fmt_rate(write_speed),
            "read_speed_raw": round(read_speed, 1),
            "write_speed_raw": round(write_speed, 1),
            "history": list(_disk_io_history[name]),
        }

    _prev_disk = current
    _prev_disk_time = now
    return Success(data=result)
