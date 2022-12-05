from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.websocket.connection_manager import (
    ConnectionManager,
    get_connection_manager,
)
from app.models.enums.event_type import EventType

router: APIRouter = APIRouter()

CONNECTION_MANAGER: ConnectionManager = get_connection_manager()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await CONNECTION_MANAGER.connect(websocket, 1, EventType.NOTIFICATION)
    try:
        while True:
            data = await websocket.receive_text()
            await CONNECTION_MANAGER.send_personal_message_with_user_id(
                data, 1, EventType.NOTIFICATION
            )
            await CONNECTION_MANAGER.send_personal_message(
                data, websocket, EventType.NOTIFICATION
            )
            print(CONNECTION_MANAGER.active_connections)
    except WebSocketDisconnect:
        CONNECTION_MANAGER.disconnect(websocket, EventType.NOTIFICATION)
