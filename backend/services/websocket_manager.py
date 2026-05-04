import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, project_id: str, ws: WebSocket):
        await ws.accept()
        self.active[project_id] = ws

    def disconnect(self, project_id: str):
        self.active.pop(project_id, None)

    async def send(self, project_id: str, data: dict):
        ws = self.active.get(project_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False))
            except Exception:
                self.disconnect(project_id)

manager = ConnectionManager()