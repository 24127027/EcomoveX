from typing import Dict, List
from fastapi import WebSocket


class SocketService:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.user_connections: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
            self.user_connections[room_id] = {}
        self.active_connections[room_id].append(websocket)
        self.user_connections[room_id][user_id] = websocket

    def disconnect(self, websocket: WebSocket, room_id: int, user_id: int):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if user_id in self.user_connections[room_id]:
                del self.user_connections[room_id][user_id]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
                del self.user_connections[room_id]

    async def broadcast(self, message: dict, room_id: int):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def send_to_user(self, message: dict, room_id: int, user_id: int):
        if room_id in self.user_connections:
            websocket = self.user_connections[room_id].get(user_id)
            if websocket:
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass

    def get_room_users(self, room_id: int) -> List[int]:
        return list(self.user_connections.get(room_id, {}).keys())


socket = SocketService()
