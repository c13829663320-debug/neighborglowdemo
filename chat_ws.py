from typing import Dict, Set, Optional
import json
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_sessions: Dict[int, Set[str]] = {}

    async def connect(self, websocket: WebSocket, group_id: str, user_id: int):
        await websocket.accept()
        if group_id not in self.active_connections:
            self.active_connections[group_id] = set()
        self.active_connections[group_id].add(websocket)
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(group_id)

    def disconnect(self, websocket: WebSocket, group_id: str, user_id: int):
        if group_id in self.active_connections:
            self.active_connections[group_id].discard(websocket)
            if not self.active_connections[group_id]:
                del self.active_connections[group_id]
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(group_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]

    async def send_to_group(self, group_id: str, message: dict):
        if group_id in self.active_connections:
            for connection in self.active_connections[group_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def send_to_user(self, user_id: int, message: dict):
        for group_id in self.user_sessions.get(user_id, set()):
            if group_id in self.active_connections:
                for connection in self.active_connections[group_id]:
                    try:
                        await connection.send_json(message)
                    except Exception:
                        pass

    async def broadcast(self, message: dict):
        for group_id in self.active_connections:
            await self.send_to_group(group_id, message)

    def get_online_count(self, group_id: str) -> int:
        return len(self.active_connections.get(group_id, set()))


manager = ConnectionManager()
