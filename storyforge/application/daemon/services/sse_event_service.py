import asyncio
from typing import Any


class SSEEventManager:
    def __init__(self) -> None:
        self.connections: list[asyncio.Queue[dict[str, Any]]] = []

    def connect(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.connections.append(queue)
        return queue

    def disconnect(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        if queue in self.connections:
            self.connections.remove(queue)

    def broadcast(self, event: dict[str, Any]) -> None:
        for queue in list(self.connections):
            queue.put_nowait(event)
