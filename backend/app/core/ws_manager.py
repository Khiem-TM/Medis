import asyncio
import json
import logging
from typing import Dict, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections per user."""

    def __init__(self) -> None:
        # user_id -> list of WebSocket (supports multiple tabs)
        self._connections: Dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)
        logger.info(f"WS connected: user_id={user_id}, total={len(self._connections[user_id])}")

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        if user_id in self._connections:
            try:
                self._connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(f"WS disconnected: user_id={user_id}")

    def is_online(self, user_id: int) -> bool:
        return user_id in self._connections and len(self._connections[user_id]) > 0

    async def send_to_user(self, user_id: int, payload: dict) -> bool:
        """Send JSON payload to all connections of a user. Returns True if delivered."""
        if not self.is_online(user_id):
            return False
        dead = []
        for ws in list(self._connections.get(user_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)
        return self.is_online(user_id)

    async def broadcast(self, payload: dict) -> None:
        """Broadcast to all connected users."""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, payload)

    @property
    def online_user_ids(self) -> list[int]:
        return list(self._connections.keys())


# Singleton instance
ws_manager = ConnectionManager()
