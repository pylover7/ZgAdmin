import time
from collections import deque

import psutil
from fastapi import APIRouter, Query

from app.models import Success
from app.utils.system_info import (
    _fmt_rate,
    get_cpu_info,
    get_disk_info,
    get_disk_io,
    get_load_info,
    get_memory_info,
    get_network_io,
    get_top_processes,
)

systemMonitorRouter = APIRouter()


class _RateTracker:
    """速率计算器 — 封装"上次采样"状态，替代 global 语句"""

    def __init__(self, history_max: int = 600) -> None:
        self._prev: dict = {}
        self._prev_time: float = 0
        self._history: dict[str, deque] = {}
        self._history_max = history_max

    def compute(
        self,
        current: dict[str, dict],
        speed_map: dict[str, str],
    ) -> dict[str, dict]:
        """计算速率并更新历史

        Args:
            current: {name: {key1: val1, key2: val2, ...}}
            speed_map: {counter_key: output_name}, 如 {"bytes_sent": "sent", "bytes_recv": "recv"}
                       输出 key 为 {name}_speed / {name}_speed_raw

        Returns:
            {name: {原始字段, *_speed, *_speed_raw, history}}
        """
        now = time.time()
        result: dict[str, dict] = {}

        for name, counters in current.items():
            rates: dict[str, float] = {}  # {output_name: rate_value}
            if name in self._prev and self._prev_time > 0:
                dt = now - self._prev_time
                if dt > 0:
                    for counter_key, out_name in speed_map.items():
                        rates[out_name] = (counters[counter_key] - self._prev[name][counter_key]) / dt

            if name not in self._history:
                self._history[name] = deque(maxlen=self._history_max)

            self._history[name].append(
                {
                    "time": round(now * 1000),
                    **{f"{k}_speed": round(v, 1) for k, v in rates.items()},
                }
            )

            result[name] = {
                **counters,
                **{f"{k}_speed_raw": round(v, 1) for k, v in rates.items()},
                **{f"{k}_speed": _fmt_rate(v) for k, v in rates.items()},
                "history": list(self._history[name]),
            }

        self._prev = current
        self._prev_time = now
        return result


# 模块级实例 — 替代 global 语句
_net_tracker = _RateTracker()
_disk_tracker = _RateTracker()


@systemMonitorRouter.get("/status")
async def system_status():
    cpu_pct = psutil.cpu_percent(interval=0)
    load = get_load_info(cpu_percent=cpu_pct)
    cpu = get_cpu_info()
    mem = get_memory_info()
    disk = get_disk_info()
    top_cpu = get_top_processes(5)
    return Success(
        data={
            "load": {
                "load1": load.load1,
                "load5": load.load5,
                "load15": load.load15,
                "status": load.status,
                "cores": load.cores,
                "percent": load.percent,
            },
            "cpu": {
                "percent": cpu.percent,
                "freq": cpu.freq,
                "per_cpu": cpu.per_cpu,
                "physical_cores": cpu.physical_cores,
                "logical_cores": cpu.logical_cores,
            },
            "memory": {
                "percent": mem.percent,
                "total": mem.total,
                "used": mem.used,
                "available": mem.available,
                "cached": mem.cached,
                "buffers": mem.buffers,
                "shared": mem.shared,
            },
            "disk": {
                "percent": disk.percent,
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
            },
            "top_cpu": [
                {"pid": p.pid, "name": p.name, "cpu_percent": p.cpu_percent, "memory_percent": p.memory_percent}
                for p in top_cpu
            ],
        }
    )


@systemMonitorRouter.get("/network")
async def network_monitor(iface: str = Query(default="")):
    current = get_network_io()
    result = _net_tracker.compute(current, {"bytes_sent": "sent", "bytes_recv": "recv"})

    if iface:
        return Success(data=result.get(iface, {}))
    return Success(data=result)


@systemMonitorRouter.get("/disk-io")
async def disk_io_monitor():
    current = get_disk_io()
    result = _disk_tracker.compute(current, {"read_bytes": "read", "write_bytes": "write"})
    return Success(data=result)
