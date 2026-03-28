from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

JobFn = Callable[[], Awaitable[Any]]


class GenerationScheduler:
    """Serializes LLM jobs: if the runtime is busy, later calls wait in FIFO order."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[tuple[JobFn, asyncio.Future[Any]]] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None
        self._processing = asyncio.Event()
        self._processing.set()

    @property
    def queue_depth(self) -> int:
        return self._queue.qsize()

    @property
    def is_busy(self) -> bool:
        return not self._processing.is_set()

    def start(self) -> None:
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._run(), name="generation-scheduler")

    async def stop(self) -> None:
        if self._worker is not None and not self._worker.done():
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
        self._worker = None

    async def submit(self, job: JobFn) -> Any:
        self.start()
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        await self._queue.put((job, fut))
        return await fut

    async def _run(self) -> None:
        while True:
            job_fn, fut = await self._queue.get()
            self._processing.clear()
            try:
                result = await job_fn()
                if not fut.done():
                    fut.set_result(result)
            except Exception as exc:
                if not fut.done():
                    fut.set_exception(exc)
            finally:
                self._processing.set()
                self._queue.task_done()
