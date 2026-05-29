from fastapi import WebSocket
from typing import List 

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket): #syntax breakdown : connect method take a websocket object as parameter and return nothing because it is async function. It just adds that accepted websocket connection to the list of active connections.
        await websocket.accept()
        self.active_connections.append(websocket)
        print("WebSocket connected. Total connections:", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("WebSocket disconnected. Remaining connections:", len(self.active_connections))


    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
