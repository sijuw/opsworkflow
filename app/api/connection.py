from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_api_token
from app.db.dependencies import get_db
from app.schemas.connection import (
    ConnectionConfigCreate,
    ConnectionConfigResponse,
    ConnectionConfigUpdate,
    ConnectionSwitchLogResponse,
    ConnectionSwitchPreviewResponse,
    ConnectionSwitchRequest,
    ConnectionSwitchResponse,
    ConnectionStatusResponse,
)
from app.services import connection_service
from app.services.aptent_client import (
    AptentAuthError,
    AptentClient,
    AptentError,
    get_aptent_client,
)
from app.services.connection_switch import DiffAssertionError, ConnectionSwitchError

# Prefix is /connections, not /api/connections: nginx proxies /api/ to /
# and strips the prefix, so mounting /api here would double it up.
router = APIRouter(
    prefix="/connections",
    tags=["Switch Institution Connection"],
    dependencies=[Depends(require_api_token)],
)


def _handle(exc: Exception) -> HTTPException:
    """Map internal failures onto responses an engineer can act on."""
    if isinstance(exc, AptentAuthError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Aptent rejected our credentials: {exc}",
        )
    if isinstance(exc, DiffAssertionError):
        # Deliberately 409: the request was valid, but applying it would have
        # changed more than the connection, so nothing was sent.
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Aborted before sending — {exc}",
        )
    if isinstance(exc, AptentError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        )
    if isinstance(exc, connection_service.ConnectionServiceError):
        msg = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in msg.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        return HTTPException(status_code=code, detail=msg)
    if isinstance(exc, ConnectionSwitchError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    raise exc


# --- configuration ---------------------------------------------------------


@router.get("/configs", response_model=list[ConnectionConfigResponse])
def list_configs(db: Session = Depends(get_db)):
    try:
        return [
            connection_service.config_payload(c) for c in connection_service.list_configs(db)
        ]
    except Exception as exc:
        raise _handle(exc)


@router.post(
    "/configs", response_model=ConnectionConfigResponse, status_code=status.HTTP_201_CREATED
)
def create_config(payload: ConnectionConfigCreate, db: Session = Depends(get_db)):
    try:
        return connection_service.config_payload(connection_service.create_config(db, payload))
    except Exception as exc:
        raise _handle(exc)


@router.put("/configs/{config_id}", response_model=ConnectionConfigResponse)
def update_config(
    config_id: int, payload: ConnectionConfigUpdate, db: Session = Depends(get_db)
):
    try:
        return connection_service.config_payload(
            connection_service.update_config(db, config_id, payload)
        )
    except Exception as exc:
        raise _handle(exc)


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(config_id: int, db: Session = Depends(get_db)):
    try:
        connection_service.delete_config(db, config_id)
    except Exception as exc:
        raise _handle(exc)


# --- live status and switching ---------------------------------------------


@router.get("/status/{config_id}", response_model=ConnectionStatusResponse)
def get_status(
    config_id: int,
    db: Session = Depends(get_db),
    client: AptentClient = Depends(get_aptent_client),
):
    try:
        return connection_service.get_status(db, client, config_id)
    except Exception as exc:
        raise _handle(exc)


@router.post("/switch/preview", response_model=ConnectionSwitchPreviewResponse)
def preview_switch(
    payload: ConnectionSwitchRequest,
    db: Session = Depends(get_db),
    client: AptentClient = Depends(get_aptent_client),
):
    """Compute the exact change without applying it.

    Not gated on CONNECTION_SWITCH_ENABLED — it writes nothing, and being able to
    see what a switch *would* do is useful while writes are still disabled.
    """
    try:
        return connection_service.preview_switch(
            db, client, payload.config_id, payload.target_route
        )
    except Exception as exc:
        raise _handle(exc)


@router.post("/switch", response_model=ConnectionSwitchResponse)
def switch(
    payload: ConnectionSwitchRequest,
    db: Session = Depends(get_db),
    client: AptentClient = Depends(get_aptent_client),
):
    if not connection_service.switching_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "connection switching is disabled. Set CONNECTION_SWITCH_ENABLED=true once "
                "status readings have been verified against the Cosmos portal."
            ),
        )
    try:
        return connection_service.execute_switch(
            db,
            client,
            payload.config_id,
            payload.target_route,
            payload.expected_from_route,
        )
    except Exception as exc:
        raise _handle(exc)


@router.get("/auth-status")
def auth_status(client: AptentClient = Depends(get_aptent_client)):
    """Is our Cosmos credential working, and when did it last work.

    Deliberately cheap and side-effect free: during an incident you want to
    tell in one call whether auth is the problem, rather than inferring it
    from a failed switch.
    """
    getter = getattr(client, "auth_status", None)
    if getter is None:
        return {"configured": False, "last_error": "client exposes no auth_status"}
    return getter()


@router.get("/history/{config_id}", response_model=list[ConnectionSwitchLogResponse])
def switch_history(config_id: int, db: Session = Depends(get_db)):
    try:
        connection_service.get_config(db, config_id)
        return connection_service.switch_history(db, config_id)
    except Exception as exc:
        raise _handle(exc)
