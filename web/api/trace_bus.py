"""In-process pub/sub for Reasoning Trace events.

Every orchestrator tick emits a sequence of structured events (`tick.start`,
`agent.output`, `policy.decision`, `trace.emitted`, `tick.end`). The
WebSocket endpoint subscribes to this bus; HTTP handlers publish into it.

Each subscriber gets its own `asyncio.Queue` so a slow client cannot back
up other consumers — events are dropped from the slow client's queue when
it overflows.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional


class TraceBus:
    """Async fan-out queue for trace events. Singleton via `bus()`."""

    def __init__(self, queue_max: int = 256) -> None:
        self._subs: List[asyncio.Queue] = []
        self._queue_max = queue_max
        self._lock = asyncio.Lock()
        self._history: List[Dict[str, Any]] = []
        self._history_max = 200

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=self._queue_max)
        async with self._lock:
            self._subs.append(q)
            # Replay recent history so a late subscriber sees the active tick.
            for evt in list(self._history)[-32:]:
                try:
                    q.put_nowait(evt)
                except asyncio.QueueFull:  # pragma: no cover - very fast subscribers only
                    break
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        async with self._lock:
            try:
                self._subs.remove(q)
            except ValueError:
                pass

    async def publish(self, event: Dict[str, Any]) -> None:
        envelope = self._envelope(event)
        async with self._lock:
            self._history.append(envelope)
            if len(self._history) > self._history_max:
                self._history = self._history[-self._history_max :]
            dead: List[asyncio.Queue] = []
            for q in self._subs:
                try:
                    q.put_nowait(envelope)
                except asyncio.QueueFull:
                    # Slow consumer — drop oldest then enqueue.
                    try:
                        q.get_nowait()
                        q.put_nowait(envelope)
                    except Exception:  # pragma: no cover
                        dead.append(q)
            for q in dead:
                try:
                    self._subs.remove(q)
                except ValueError:
                    pass

    @staticmethod
    def _envelope(event: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event_id": "ev_" + uuid.uuid4().hex[:12],
            "ts": time.time(),
            **event,
        }

    @property
    def subscriber_count(self) -> int:
        return len(self._subs)

    def history(self) -> List[Dict[str, Any]]:
        return list(self._history)


_BUS: Optional[TraceBus] = None


def bus() -> TraceBus:
    global _BUS
    if _BUS is None:
        _BUS = TraceBus()
    return _BUS


def reset_bus() -> None:
    """Test helper — drop all subscribers."""
    global _BUS
    _BUS = TraceBus()
