from __future__ import annotations

from dataclasses import dataclass

try:
    import pynvml
except ImportError:  # pragma: no cover
    pynvml = None  # type: ignore[assignment]


@dataclass(frozen=True)
class GpuDeviceStats:
    utilization_percent: float
    vram_used_bytes: int
    vram_total_bytes: int


_nvml_initialized = False


def _ensure_nvml() -> bool:
    global _nvml_initialized
    if pynvml is None:
        return False
    if not _nvml_initialized:
        try:
            pynvml.nvmlInit()
            _nvml_initialized = True
        except Exception:
            return False
    return True


def get_primary_gpu_stats() -> GpuDeviceStats | None:
    if not _ensure_nvml():
        return None
    assert pynvml is not None
    try:
        count = pynvml.nvmlDeviceGetCount()
        if count < 1:
            return None
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return GpuDeviceStats(
            utilization_percent=float(util.gpu),
            vram_used_bytes=int(mem.used),
            vram_total_bytes=int(mem.total),
        )
    except Exception:
        return None
