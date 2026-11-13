"""Lightweight circuit breaker and per-supplier sliding-window limiter."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any


class CircuitOpenError(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_seconds: float = 30.0):
        if failure_threshold < 1 or recovery_seconds <= 0:
            raise ValueError("threshold and recovery period must be positive")
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failures = 0
        self.opened_at: float | None = None
        self._probe_lock = asyncio.Lock()

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "CLOSED"
        if time.monotonic() - self.opened_at >= self.recovery_seconds:
            return "HALF_OPEN"
        return "OPEN"

    async def call(self, operation: Callable[[], Awaitable[Any]]) -> Any:
        if self.state == "OPEN":
            raise CircuitOpenError("Supplier circuit is open; try again after cooldown")
        if self.state == "HALF_OPEN":
            async with self._probe_lock:
                if self.state == "OPEN":
                    raise CircuitOpenError("Supplier recovery probe is already running")
                return await self._execute(operation)
        return await self._execute(operation)

    async def _execute(self, operation: Callable[[], Awaitable[Any]]) -> Any:
        try:
            result = await operation()
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.opened_at = time.monotonic()
            raise
        self.failures = 0
        self.opened_at = None
        return result


class SlidingWindowRateLimiter:
    def __init__(self):
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: float = 1.0, now: float | None = None) -> bool:
        if limit < 1 or window_seconds <= 0:
            raise ValueError("limit and window must be positive")
        timestamp = time.monotonic() if now is None else now
        events = self._events[key]
        while events and timestamp - events[0] >= window_seconds:
            events.popleft()
        if len(events) >= limit:
            return False
        events.append(timestamp)
        return True
