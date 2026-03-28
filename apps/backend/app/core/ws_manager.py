from fastapi import WebSocket

# Memory dict tracking progress by model_id
# Fields: progress, downloaded, total, speed, status
download_progress: dict[int, dict] = {}

class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, model_id: int) -> None:
        await websocket.accept()
        if model_id not in self.active_connections:
            self.active_connections[model_id] = []
        self.active_connections[model_id].append(websocket)

    def disconnect(self, websocket: WebSocket, model_id: int) -> None:
        if model_id in self.active_connections:
            if websocket in self.active_connections[model_id]:
                self.active_connections[model_id].remove(websocket)
            if not self.active_connections[model_id]:
                del self.active_connections[model_id]

    async def send(self, websocket: WebSocket, message: dict) -> None:
        await websocket.send_json(message)

    async def send_to(self, model_id: int, message: dict) -> None:
        if model_id in self.active_connections:
            for connection in self.active_connections[model_id]:
                try:
                    await self.send(connection, message)
                except Exception:
                    # Ignore disconnected sockets during broadcast
                    pass

ws_manager = WebSocketManager()
