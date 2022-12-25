from databases import Database
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)

from app.core.database.mysql_driver import get_mysql_driver
from app.core.websocket.connection_manager import (
    ConnectionManager,
    get_connection_manager,
)
from app.exceptions import base as base_exceptions, user_meta as user_meta_exceptions
from app.models.enums.event_type import EventType
from app.models.user import DBUserToken
from app.models.user_meta import DBUserMeta
from app.services.dependencies import ws_fetch_db_user_from_token

router: APIRouter = APIRouter()

CONNECTION_MANAGER: ConnectionManager = get_connection_manager()


@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    db_user_token: DBUserToken = Depends(ws_fetch_db_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
):
    db_user_meta: DBUserMeta = await DBUserMeta.get_by(
        mysql_driver, "user_id", db_user_token.id
    )

    # It seems like FastAPI doesn't support WebSocketException before websocket.accept()
    # even if in the docs it says that it does. Think about it and find a workaround.
    if not db_user_meta.has_push_notifications:
        raise WebSocketException(
            user_meta_exceptions.DoesNotHavePushNotificationsException().status_code,
            user_meta_exceptions.DoesNotHavePushNotificationsException().description,
        )

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
