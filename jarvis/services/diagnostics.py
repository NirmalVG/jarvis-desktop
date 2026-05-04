"""
jarvis/services/diagnostics.py
═══════════════════════════════
Real-time system diagnostics for the HUD overlay.

Provides CPU, memory, disk, uptime, and network metrics
in a compact dict suitable for WebSocket broadcast.

PRD references: F006 (HUD UI), M5 (System diagnostics)
"""

import platform
import time
from datetime import datetime

_BOOT_TIME: float | None = None


def _get_boot_time() -> float:
    """Return system boot time as a Unix timestamp."""
    global _BOOT_TIME
    if _BOOT_TIME is not None:
        return _BOOT_TIME

    try:
        import psutil
        _BOOT_TIME = psutil.boot_time()
    except ImportError:
        _BOOT_TIME = time.time()  # fallback: use app start time
    return _BOOT_TIME


def get_system_info() -> dict:
    """
    Collect system metrics. Returns a flat dict suitable for JSON broadcast.

    Uses psutil if available; degrades gracefully without it.
    Fields returned:
        cpu_percent      — overall CPU usage (0–100)
        memory_percent   — RAM usage (0–100)
        memory_used_gb   — RAM used in GB
        memory_total_gb  — total RAM in GB
        disk_percent     — primary disk usage (0–100)
        uptime_hours     — system uptime in hours
        platform         — OS name
        python_version   — Python runtime version
        timestamp        — ISO timestamp
    """
    info = {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "timestamp": datetime.now().isoformat(),
    }

    try:
        import psutil

        # CPU
        info["cpu_percent"] = psutil.cpu_percent(interval=0)

        # Memory
        mem = psutil.virtual_memory()
        info["memory_percent"] = mem.percent
        info["memory_used_gb"] = round(mem.used / (1024 ** 3), 1)
        info["memory_total_gb"] = round(mem.total / (1024 ** 3), 1)

        # Disk
        try:
            disk = psutil.disk_usage("/")
            info["disk_percent"] = disk.percent
        except Exception:
            info["disk_percent"] = 0

        # Uptime
        boot = _get_boot_time()
        info["uptime_hours"] = round((time.time() - boot) / 3600, 1)

    except ImportError:
        # psutil not installed — provide minimal info
        info["cpu_percent"] = 0
        info["memory_percent"] = 0
        info["memory_used_gb"] = 0
        info["memory_total_gb"] = 0
        info["disk_percent"] = 0
        info["uptime_hours"] = 0

    return info
