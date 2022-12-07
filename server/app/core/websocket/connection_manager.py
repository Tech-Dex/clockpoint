from fastapi import WebSocket

from app.core.singleton import SingletonMeta
from app.models.enums.event_type import EventType
from app.schemas.v1.response import WebsocketResponse


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

    async def broadcast(self, message: dict, event_type: str, scope: str = "undefined"):
        for connection in self.active_connections[event_type]:
            await connection["connection"].send_text(
                self.format_message(message, scope)
            )

    async def send_personal_message(
        self,
        message: dict,
        websocket: WebSocket,
        event_type: str,
        scope: str = "undefined",
    ):
        for connection in self.active_connections[event_type]:
            if connection["connection"] == websocket:
                await connection["connection"].send_text(
                    self.format_message(message, scope)
                )
                break

    async def send_personal_message_with_user_id(
        self, message: dict, user_id: int, event_type: str, scope: str = "undefined"
    ):
        for connection in self.active_connections[event_type]:
            if connection["user_id"] == user_id:
                await connection["connection"].send_text(
                    self.format_message(message, scope)
                )
                break

    @staticmethod
    def format_message(message: dict, scope: str) -> str:
        return WebsocketResponse(scope=scope, payload=message).json()


CONNECTION_MANAGER: ConnectionManager = ConnectionManager()


def get_connection_manager():
    return CONNECTION_MANAGER
