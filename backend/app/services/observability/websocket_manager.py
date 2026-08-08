"""WebSocketManager — manages real-time WebSocket subscriptions and metrics broadcasting."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
import uuid

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("cloudpilot.websocket_manager")


class WebSocketManager:
    """Manages active WebSocket connections per deployment_id and broadcasts live metrics."""

    def __init__(self) -> None:
        # deployment_id_str -> set of active WebSockets
        self._subscriptions: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, deployment_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            if deployment_id not in self._subscriptions:
                self._subscriptions[deployment_id] = set()
            self._subscriptions[deployment_id].add(websocket)
        logger.info(f"WebSocket client connected to deployment {deployment_id}.")

    async def disconnect(self, deployment_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            if deployment_id in self._subscriptions:
                self._subscriptions[deployment_id].discard(websocket)
                if not self._subscriptions[deployment_id]:
                    del self._subscriptions[deployment_id]
        logger.info(f"WebSocket client disconnected from deployment {deployment_id}.")

    async def broadcast_metrics(self, deployment_id: str, data: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._subscriptions.get(deployment_id, []))

        if not sockets:
            return

        payload = json.dumps({
            "type": "metrics.update",
            "deployment_id": deployment_id,
            "data": data,
        })

        dead_sockets: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_sockets.append(ws)

        if dead_sockets:
            async with self._lock:
                for ws in dead_sockets:
                    self._subscriptions.get(deployment_id, set()).discard(ws)


# Global singleton manager instance
ws_manager = WebSocketManager()
