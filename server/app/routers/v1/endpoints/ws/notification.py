from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.websocket.connection_manager import (
    ConnectionManager,
    get_connection_manager,
)
from app.exceptions import base as base_exceptions
from app.models.enums.event_type import EventType
from app.models.user import DBUserToken
from app.services.dependencies import ws_fetch_db_user_from_token

router: APIRouter = APIRouter()

CONNECTION_MANAGER: ConnectionManager = get_connection_manager()


@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    db_user_token: DBUserToken = Depends(ws_fetch_db_user_from_token),
):
    await CONNECTION_MANAGER.connect(
        websocket, db_user_token.id, EventType.NOTIFICATION
    )
    try:
        while True:
            _ = await websocket.receive_text()
            await CONNECTION_MANAGER.send_personal_message(
                {"message": base_exceptions.NotImplementedException.description},
                websocket,
                EventType.NOTIFICATION,
            )
    except WebSocketDisconnect:
        CONNECTION_MANAGER.disconnect(websocket, EventType.NOTIFICATION)
