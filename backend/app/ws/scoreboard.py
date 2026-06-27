
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from ..core import redis_pubsub

# Global set of connected websockets
connections: set[WebSocket] = set()

async def broadcast(message: dict):
    data = json.dumps(message)
    await asyncio.gather(*[ws.send_text(data) for ws in connections])

async def publish_score_update(team_id: str, points: int):
    await broadcast({"type": "score_update", "team_id": team_id, "points": points})

async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    try:
        # keep alive loop
        while True:
            await ws.receive_text()  # we don't expect client messages; just keep alive
    except WebSocketDisconnect:
        connections.remove(ws)

# backend/app/ws/__init__.py
from fastapi import APIRouter, WebSocket
from .scoreboard import websocket_endpoint

router = APIRouter()
router.websocket("/ws/scoreboard")(websocket_endpoint)
