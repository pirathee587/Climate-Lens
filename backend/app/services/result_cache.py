"""Bounded application-local immutable results; monotonic TTL and FIFO eviction."""

import time
from collections import OrderedDict
from collections.abc import Callable, Sequence
from threading import RLock
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request

from app.core.errors import APIError
from app.schemas.analysis import AnalysisResponse

MAX_ENTRY_BYTES = 2 * 1024 * 1024
MAX_CACHE_BYTES = 32 * 1024 * 1024


class ResultCache:
    def __init__(
        self,
        *,
        ttl_seconds: int = 1200,
        max_entries: int = 100,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 86400:
            raise ValueError("cache TTL must be an integer in 1..86400 seconds")
        if type(max_entries) is not int or not 2 <= max_entries <= 1000:
            raise ValueError("cache capacity must be an integer in 2..1000")
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._clock = clock
        self._lock = RLock()
        self._entries: OrderedDict[UUID, tuple[float, bytes]] = OrderedDict()
        self._bytes = 0

    def _remove(self, key: UUID) -> None:
        _, payload = self._entries.pop(key)
        self._bytes -= len(payload)

    def _expire(self, now: float) -> None:
        for key, (deadline, _) in tuple(self._entries.items()):
            if now >= deadline:
                self._remove(key)

    def put_many(self, results: Sequence[AnalysisResponse]) -> None:
        """Validate the whole batch before atomically publishing any result."""
        if not 1 <= len(results) <= self.max_entries:
            raise ValueError("invalid cache batch size")
        prepared = []
        for result in results:
            # Reparse dumps: Pydantic instances may contain mutated nested lists.
            checked = AnalysisResponse.model_validate(
                result.model_dump(warnings="error")
            )
            payload = checked.model_dump_json().encode("utf-8")
            if len(payload) > MAX_ENTRY_BYTES:
                raise ValueError("analysis exceeds cache entry size limit")
            prepared.append((checked.analysis_id, payload))
        if len({key for key, _ in prepared}) != len(prepared):
            raise ValueError("duplicate analysis IDs in batch")
        batch_bytes = sum(len(payload) for _, payload in prepared)
        if batch_bytes > MAX_CACHE_BYTES:
            raise ValueError("analysis batch exceeds cache byte limit")
        with self._lock:
            now = self._clock()
            self._expire(now)
            for key, _ in prepared:
                if key in self._entries:
                    self._remove(key)
            while self._entries and (
                len(self._entries) + len(prepared) > self.max_entries
                or self._bytes + batch_bytes > MAX_CACHE_BYTES
            ):
                self._remove(next(iter(self._entries)))
            for key, payload in prepared:
                self._entries[key] = (now + self.ttl_seconds, payload)
                self._bytes += len(payload)

    def get(self, analysis_id: UUID) -> AnalysisResponse:
        with self._lock:
            self._expire(self._clock())
            entry = self._entries.get(analysis_id)
            if entry is None:
                raise APIError(404, "NOT_FOUND", "Resource not found.")
            payload = entry[1]
        # Fresh nested objects each time; reads do not extend TTL or FIFO order.
        return AnalysisResponse.model_validate_json(payload)

    def __len__(self) -> int:
        with self._lock:
            self._expire(self._clock())
            return len(self._entries)


def get_result_cache(request: Request) -> ResultCache:
    return request.app.state.result_cache


def get_cached_analysis(
    analysis_id: UUID,
    cache: Annotated[ResultCache, Depends(get_result_cache)],
) -> AnalysisResponse:
    return cache.get(analysis_id)
