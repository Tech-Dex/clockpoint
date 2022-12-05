from fastapi import WebSocket

from app.core.singleton import SingletonMeta
from app.models.enums.event_type import EventType


class ConnectionManager(metaclass=SingletonMeta):
    """
    Store connection with the following structure:
    {
    "notifications":  [
        {
            "user_id": "connection",
        },
        {
            "user_id": "connection",
        },
    ],
    "event_type": [...]
    }
    """

    def __init__(self):
        self.active_connections: dict = {}
        for event_type in EventType.list():
            self.active_connections[event_type] = []

    async def connect(self, websocket: WebSocket, user_id: int, event_type: str):
        await websocket.accept()
        self.active_connections[event_type].append(
            {"user_id": user_id, "connection": websocket}
        )

    def disconnect(self, websocket: WebSocket, event_type: str) -> bool:
        for connection in self.active_connections[event_type]:
            if connection["connection"] == websocket:
                self.active_connections[event_type].remove(connection)
                return True
        return False

    def disconnect_with_user_id(self, user_id: int, event_type: str) -> bool:
        for connection in self.active_connections[event_type]:
            if connection["user_id"] == user_id:
                self.active_connections[event_type.value].remove(connection)
                return True
        return False

    async def broadcast(self, message: str, event_type: str):
        for connection in self.active_connections[event_type]:
            await connection["connection"].send_text(message)

    async def send_personal_message(
        self, message: str, websocket: WebSocket, event_type: str
    ):
        for connection in self.active_connections[event_type]:
            if connection["connection"] == websocket:
                await connection["connection"].send_text(message)
                break

    async def send_personal_message_with_user_id(
        self, message: str, user_id: int, event_type: str
    ):
        for connection in self.active_connections[event_type]:
            if connection["user_id"] == user_id:
                await connection["connection"].send_text(message)
                break


def get_connection_manager():
    return ConnectionManager()
