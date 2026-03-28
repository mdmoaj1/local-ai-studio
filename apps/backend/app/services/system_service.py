from __future__ import annotations

from dataclasses import dataclass

import psutil

from app.utils.gpu import get_primary_gpu_stats


@dataclass(frozen=True)
class SystemMetricsSnapshot:
    """Utilization 0–100; totals in bytes for RAM/VRAM."""

    cpu_percent: float
    ram_percent: float
    gpu_percent: float
    vram_percent: float
    ram_total_bytes: int
    ram_used_bytes: int
    vram_total_bytes: int
    vram_used_bytes: int

    def as_ws_payload(self) -> dict[str, float | int]:
        return {
            "cpu": round(self.cpu_percent, 2),
            "ram": round(self.ram_percent, 2),
            "gpu": round(self.gpu_percent, 2),
            "vram": round(self.vram_percent, 2),
            "ram_total_bytes": int(self.ram_total_bytes),
            "ram_used_bytes": int(self.ram_used_bytes),
            "vram_total_bytes": int(self.vram_total_bytes),
            "vram_used_bytes": int(self.vram_used_bytes),
        }


class SystemService:
    """psutil + pynvml system metrics (REST + WebSocket)."""

    def snapshot(self) -> SystemMetricsSnapshot:
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        ram_pct = float(vm.percent)
        ram_total = int(vm.total)
        ram_used = int(vm.used)

        gpu_stats = get_primary_gpu_stats()
        if gpu_stats is None or gpu_stats.vram_total_bytes <= 0:
            gpu_pct = 0.0
            vram_pct = 0.0
            vram_total = 0
            vram_used = 0
        else:
            gpu_pct = max(0.0, min(100.0, float(gpu_stats.utilization_percent)))
            vram_total = int(gpu_stats.vram_total_bytes)
            vram_used = int(gpu_stats.vram_used_bytes)
            vram_pct = (vram_used / vram_total * 100.0) if vram_total > 0 else 0.0

        return SystemMetricsSnapshot(
            cpu_percent=max(0.0, min(100.0, cpu)),
            ram_percent=max(0.0, min(100.0, ram_pct)),
            gpu_percent=gpu_pct,
            vram_percent=max(0.0, min(100.0, vram_pct)),
            ram_total_bytes=ram_total,
            ram_used_bytes=ram_used,
            vram_total_bytes=vram_total,
            vram_used_bytes=vram_used,
        )
