from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable, Callable
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.model_manager import ModelManager
from app.core.model_registry import ModelKind, ModelStatus
from app.db.models import AdapterRecord, History, StudioModel
from app.db.session import AsyncSessionLocal
from app.schemas.llm import LLMStatusResponse
from app.services.scheduler import GenerationScheduler


class LLMService:
    def __init__(self, model_manager: ModelManager, scheduler: GenerationScheduler) -> None:
        self._mgr = model_manager
        self._sched = scheduler

    @property
    def scheduler(self) -> GenerationScheduler:
        return self._sched

    def start_scheduler(self) -> None:
        self._sched.start()

    async def stop_scheduler(self) -> None:
        await self._sched.stop()

    async def load(self, session: AsyncSession, model_id: int) -> None:
        row = await session.get(StudioModel, model_id)
        if row is None:
            raise ValueError("Model not found")
        if row.status != ModelStatus.INSTALLED:
            raise ValueError("Model is not installed on disk")
        if row.model_type != ModelKind.LLM:
            raise ValueError("Only LLM (Transformers) models can be loaded through this runner today")

        current = self._mgr.get_loaded_model_id()
        if current == model_id:
            return
        if current is not None:
            await self._mgr.unload()

        await self._mgr.load_transformers(model_id, Path(row.local_path))

    async def unload(self) -> None:
        await self._mgr.unload()

    async def load_adapter(self, session: AsyncSession, adapter_id: int) -> None:
        row = await session.get(AdapterRecord, adapter_id)
        if row is None:
            raise ValueError("Adapter not found")
        from app.services.adapter_service import get_adapter_service

        path = get_adapter_service().validate_adapter_path(row)
        if self._mgr.get_loaded_model_id() is None:
            raise ValueError("Load a base model first (POST /llm/load)")

        async def job() -> None:
            await self._mgr.load_adapter(path)

        await self._sched.submit(job)

    async def _build_prompt(self, session: AsyncSession, plugin_id: int | None, user_text: str) -> str:
        if plugin_id is None:
            return user_text
        from app.services.plugin_service import get_plugin_service

        return await get_plugin_service().compose_prompt(session, plugin_id, user_text)

    async def generate(
        self,
        model_id: int,
        prompt: str,
        max_tokens: int,
        plugin_id: int | None,
        session: AsyncSession,
    ) -> str:
        async def job() -> str:
            final_prompt = await self._build_prompt(session, plugin_id, prompt)
            if self._mgr.get_loaded_model_id() != model_id:
                raise ValueError("Requested model is not the active loaded model; call POST /llm/load first")
            fn = functools.partial(self._mgr.generate_sync, final_prompt, max_tokens=max_tokens)
            text = await asyncio.to_thread(fn)
            async with AsyncSessionLocal() as hist_session:
                hist_session.add(
                    History(
                        model_id=model_id,
                        prompt=prompt,
                        response=text,
                    ),
                )
                await hist_session.commit()
            return text

        return await self._sched.submit(job)

    async def stream_generate(
        self,
        model_id: int,
        user_prompt: str,
        max_tokens: int,
        plugin_id: int | None,
        session: AsyncSession,
        on_token: Callable[[str], Awaitable[None]],
    ) -> str:
        final_prompt = await self._build_prompt(session, plugin_id, user_prompt)
        if self._mgr.get_loaded_model_id() != model_id:
            raise ValueError("Requested model is not the active loaded model; call POST /llm/load first")

        loop = asyncio.get_running_loop()
        chunk_queue: asyncio.Queue[str | None] = asyncio.Queue()

        def on_chunk_sync(chunk: str) -> None:
            asyncio.run_coroutine_threadsafe(chunk_queue.put(chunk), loop)

        async def producer() -> None:
            try:

                def blocking() -> str:
                    return self._mgr.generate_stream_sync(
                        final_prompt,
                        max_tokens=max_tokens,
                        on_chunk=on_chunk_sync,
                    )

                await asyncio.to_thread(blocking)
            finally:
                await chunk_queue.put(None)

        async def consumer() -> str:
            parts: list[str] = []
            while True:
                t = await chunk_queue.get()
                if t is None:
                    break
                parts.append(t)
                await on_token(t)
            return "".join(parts)

        prod = asyncio.create_task(producer())
        try:
            text = await consumer()
        finally:
            await prod

        async with AsyncSessionLocal() as hist_session:
            hist_session.add(
                History(
                    model_id=model_id,
                    prompt=user_prompt,
                    response=text,
                ),
            )
            await hist_session.commit()
        return text

    def status(self) -> LLMStatusResponse:
        mem = self._mgr.memory_snapshot_mb()
        return LLMStatusResponse(
            loaded_model_id=self._mgr.get_loaded_model_id(),
            backend=self._mgr.get_backend(),
            device=self._mgr.device_label(),
            cuda_available=self._mgr.cuda_available(),
            queue_depth=self._sched.queue_depth,
            busy=self._sched.is_busy,
            memory=mem,
        )


_llm_singleton: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_singleton
    if _llm_singleton is None:
        _llm_singleton = LLMService(
            model_manager=ModelManager(get_settings()),
            scheduler=GenerationScheduler(),
        )
    return _llm_singleton
