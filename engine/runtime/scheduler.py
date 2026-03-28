"""Serial background execution for GPU training (off the asyncio event loop).

JobManager enqueues work here. Future QLoRA, DeepSpeed, and multi-GPU flows can
swap the thread callable for a subprocess without changing REST/WebSocket APIs.
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable

JobFn = Callable[[], None]


class TrainingThreadScheduler:
    """Single worker thread processing a FIFO queue of training jobs."""

    def __init__(self) -> None:
        self._q: queue.Queue[JobFn | None] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return

            def _run() -> None:
                while True:
                    fn = self._q.get()
                    try:
                        if fn is None:
                            break
                        fn()
                    finally:
                        self._q.task_done()

            self._thread = threading.Thread(target=_run, name="training-scheduler", daemon=True)
            self._thread.start()

    def submit(self, fn: JobFn) -> None:
        self.start()
        self._q.put(fn)

    def shutdown(self) -> None:
        with self._lock:
            alive = self._thread is not None and self._thread.is_alive()
        if not alive:
            return
        self._q.put(None)
        if self._thread is not None:
            self._thread.join(timeout=30.0)
        self._thread = None
