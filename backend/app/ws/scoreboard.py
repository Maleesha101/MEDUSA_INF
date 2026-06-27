from __future__ import annotations

import json
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.endpoints import WebSocketEndpoint

router = APIRouter()


class ConnectionManager:
    """Tracks active WebSocket connections and broadcasts JSON payloads."""
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, data: Dict):
        payload = json.dumps(data)
        for ws in list(self.active):
            try:
                await ws.send_text(payload)
            except WebSocketDisconnect:
                self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws/scoreboard")
class ScoreboardSocket(WebSocketEndpoint):
    encoding = "json"

    async def on_connect(self, websocket: WebSocket) -> None:
        await manager.connect(websocket)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        manager.disconnect(websocket)

    async def on_receive(self, websocket: WebSocket, data: dict) -> None:
        # The client never sends data; keepalive ping is enough.
        pass

# Helper for other modules to push an update:
async def push_scoreboard_update(scoreboard: list[dict]) -> None:
    """Called after a solve is recorded – pushes the whole leaderboard."""
    await manager.broadcast({"type": "leaderboard", "data": scoreboard})
