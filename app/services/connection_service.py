"""Orchestration for the institution connection switcher.

Sits between the router, the database and Cosmos. All the byte-level safety
logic lives in app.services.connection_switch; this module decides *when* to
apply it, records what happened, and never lets an unverified write go out.
"""

import json
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.connection import (
    ConnectionConfig,
    ConnectionRoute,
    ConnectionRouteEndpoint,
    ConnectionSwitchLog,
)
from app.services.aptent_client import AptentClient, AptentError
from app.services.connection_switch import (
    PRIMARY,
    REMOTE_URL,
    SECONDARY,
    SINK_CONNECTIONS,
    UNKNOWN,
    DiffAssertionError,
    Endpoint,
    ConnectionSwitchError,
    apply_switch,
    assert_only_connection_changed,
    endpoint_for,
    identify_route,
    medium_label,
    normalise_type,
    read_current,
    strategy_for,
    summarise,
)

# Socket interchanges re-establish on their polling interval rather than
# immediately; NIBSS_2 carries pollingInterval 30000ms.
SOCKET_RECONNECT_SECONDS = 30


class ConnectionServiceError(Exception):
    """A switch could not be performed. Message is safe to show a user."""


def switching_enabled() -> bool:
    """Read per-call so the flag can be flipped without a rebuild."""
    return os.getenv("CONNECTION_SWITCH_ENABLED", "false").strip().lower() == "true"


# --- config CRUD -----------------------------------------------------------


def _route(config: ConnectionConfig, name: str) -> ConnectionRoute | None:
    return next((r for r in config.routes if r.name == name), None)


def _endpoints(config: ConnectionConfig, name: str) -> list[Endpoint]:
    route = _route(config, name)
    if not route:
        return []
    rows = sorted(route.endpoints, key=lambda e: e.sort_order)
    return [Endpoint(host=r.host, port=r.port) for r in rows]


def _medium(config: ConnectionConfig, name: str) -> str | None:
    route = _route(config, name)
    return route.medium if route else None


def _route_payload(config: ConnectionConfig, name: str) -> dict:
    route = _route(config, name)
    return {
        "medium": route.medium if route else "OTHER",
        "medium_label": medium_label(route.medium if route else None),
        "medium_note": route.medium_note if route else None,
        "medium_updated_at": route.updated_at if route else None,
        "endpoints": [
            {"host": e.host, "port": e.port}
            for e in sorted(route.endpoints, key=lambda e: e.sort_order)
        ]
        if route
        else [],
    }


def _validate_routes(
    interchange_type: str,
    primary: list[Endpoint],
    secondary: list[Endpoint],
) -> None:
    strategy = strategy_for(interchange_type)  # raises on unknown type

    for label, eps in (("primary", primary), ("secondary", secondary)):
        if not eps:
            raise ConnectionServiceError(f"{label} route must have at least one connection")

        if strategy == REMOTE_URL:
            if len(eps) != 1:
                raise ConnectionServiceError(
                    f"REST interchanges switch a single port, but {label} has "
                    f"{len(eps)} connections"
                )
        else:
            missing = [str(e) for e in eps if not e.host]
            if missing:
                raise ConnectionServiceError(
                    f"{label} route needs a host on every connection "
                    f"(socket interchange); missing on: {', '.join(missing)}"
                )

    if strategy == SINK_CONNECTIONS and len(primary) != len(secondary):
        # Guards the pool-collapse case: a three-socket institution must have a
        # three-socket alternate, or switching would silently shrink it.
        raise ConnectionServiceError(
            f"Route sizes differ ({len(primary)} vs {len(secondary)}). A "
            f"connection pool must keep the same number of connections after "
            f"a switch."
        )


def _upsert_route(
    db: Session, config: ConnectionConfig, name: str, data
) -> None:
    """Create or replace a route and its whole endpoint list."""
    eps = [Endpoint(e.host, e.port) for e in data.endpoints]

    route = _route(config, name)
    if route is None:
        route = ConnectionRoute(name=name, medium=data.medium)
        config.routes.append(route)

    route.medium = data.medium
    route.medium_note = data.medium_note

    for row in list(route.endpoints):
        route.endpoints.remove(row)
        db.delete(row)
    for i, ep in enumerate(eps):
        route.endpoints.append(
            ConnectionRouteEndpoint(host=ep.host, port=ep.port, sort_order=i)
        )


def list_configs(db: Session) -> list[ConnectionConfig]:
    return list(db.scalars(select(ConnectionConfig).order_by(ConnectionConfig.institution_name)))


def get_config(db: Session, config_id: int) -> ConnectionConfig:
    config = db.get(ConnectionConfig, config_id)
    if not config:
        raise ConnectionServiceError(f"Connection config {config_id} not found")
    return config


def create_config(db: Session, data) -> ConnectionConfig:
    primary = [Endpoint(e.host, e.port) for e in data.primary.endpoints]
    secondary = [Endpoint(e.host, e.port) for e in data.secondary.endpoints]
    _validate_routes(data.interchange_type, primary, secondary)

    existing = db.scalar(
        select(ConnectionConfig).where(
            ConnectionConfig.interchange_id == data.interchange_id
        )
    )
    if existing:
        raise ConnectionServiceError(
            f"Interchange {data.interchange_id} is already configured "
            f"({existing.institution_name})"
        )

    config = ConnectionConfig(
        institution_name=data.institution_name,
        interchange_id=data.interchange_id,
        interchange_type=normalise_type(data.interchange_type),
        institution_id=data.institution_id,
        is_active=data.is_active,
    )
    db.add(config)
    _upsert_route(db, config, PRIMARY, data.primary)
    _upsert_route(db, config, SECONDARY, data.secondary)
    db.commit()
    db.refresh(config)
    return config


def update_config(db: Session, config_id: int, data) -> ConnectionConfig:
    config = get_config(db, config_id)

    interchange_type = data.interchange_type or config.interchange_type
    primary = (
        [Endpoint(e.host, e.port) for e in data.primary.endpoints]
        if data.primary is not None
        else _endpoints(config, PRIMARY)
    )
    secondary = (
        [Endpoint(e.host, e.port) for e in data.secondary.endpoints]
        if data.secondary is not None
        else _endpoints(config, SECONDARY)
    )
    _validate_routes(interchange_type, primary, secondary)

    if data.institution_name is not None:
        config.institution_name = data.institution_name
    if data.interchange_type is not None:
        config.interchange_type = normalise_type(data.interchange_type)
    if data.institution_id is not None:
        config.institution_id = data.institution_id
    if data.is_active is not None:
        config.is_active = data.is_active
    if data.primary is not None:
        _upsert_route(db, config, PRIMARY, data.primary)
    if data.secondary is not None:
        _upsert_route(db, config, SECONDARY, data.secondary)

    db.commit()
    db.refresh(config)
    return config


def delete_config(db: Session, config_id: int) -> None:
    db.delete(get_config(db, config_id))
    db.commit()


def config_payload(config: ConnectionConfig) -> dict:
    return {
        "id": config.id,
        "institution_name": config.institution_name,
        "interchange_id": config.interchange_id,
        "interchange_type": config.interchange_type,
        "institution_id": config.institution_id,
        "is_active": config.is_active,
        "strategy": strategy_for(config.interchange_type),
        "primary": _route_payload(config, PRIMARY),
        "secondary": _route_payload(config, SECONDARY),
    }


# --- live reads ------------------------------------------------------------


def _find_live(client: AptentClient, interchange_id: int) -> tuple[dict, dict]:
    """Return (wrapper, config) for one interchange from the live list."""
    try:
        items = client.fetch_interchanges()
    except AptentError:
        raise
    except Exception as exc:  # noqa: BLE001 - normalise transport surprises
        raise AptentError(f"Could not read interchanges from Cosmos: {exc}") from exc

    for item in items or []:
        cfg = item.get("config") or {}
        if cfg.get("id") == interchange_id:
            return item, cfg

    raise ConnectionServiceError(
        f"Interchange {interchange_id} was not found in Cosmos. It may have "
        f"been removed, or the configured id is wrong."
    )


def _resolve(config: ConnectionConfig, client: AptentClient):
    """Load live state and work out where the interchange currently points."""
    wrapper, cfg = _find_live(client, config.interchange_id)

    # Trust the live typeName over the stored copy — if an interchange was
    # converted, the stored value is stale and the strategy would be wrong.
    live_type = normalise_type(cfg.get("typeName"))
    strategy = strategy_for(live_type)

    isd = cfg.get("interchangeSpecificData") or ""
    current = read_current(isd, strategy)
    primary = _endpoints(config, PRIMARY)
    secondary = _endpoints(config, SECONDARY)
    route = identify_route(current, primary, secondary)

    return wrapper, cfg, live_type, strategy, isd, current, primary, secondary, route


def get_status(db: Session, client: AptentClient, config_id: int) -> dict:
    config = get_config(db, config_id)
    (
        wrapper,
        cfg,
        live_type,
        strategy,
        isd,
        current,
        primary,
        secondary,
        route,
    ) = _resolve(config, client)

    note = None
    if route == UNKNOWN:
        note = (
            f"Live connection ({summarise(current)}) matches neither configured "
            f"route. Resolve this in Cosmos before switching."
        )
    elif live_type != config.interchange_type:
        note = (
            f"Cosmos reports type {live_type!r} but this config stores "
            f"{config.interchange_type!r}."
        )

    return {
        "config_id": config.id,
        "institution_name": config.institution_name,
        "interchange_id": config.interchange_id,
        "interchange_type": live_type,
        "strategy": strategy,
        "active_route": route,
        # Null for UNKNOWN: we do not know what the live value runs over, and
        # guessing is exactly what this field exists to prevent.
        "active_medium": _medium(config, route) if route != UNKNOWN else None,
        "active_medium_label": (
            medium_label(_medium(config, route)) if route != UNKNOWN else None
        ),
        "current": [{"host": e.host, "port": e.port} for e in current],
        "current_summary": summarise(current),
        "primary": _route_payload(config, PRIMARY),
        "secondary": _route_payload(config, SECONDARY),
        "running": wrapper.get("running"),
        "switchable": route != UNKNOWN,
        "note": note,
    }


# --- the switch ------------------------------------------------------------


def _specific_data(isd: str) -> dict:
    """Build the `specificData` sibling exactly as the portal does.

    Verified against both captured POST bodies: it is the parsed
    interchangeSpecificData with "$$hashKey" removed from each
    sinkConnections entry. The string form keeps the key; this one does not.
    """
    parsed = json.loads(isd)
    for conn in parsed.get("sinkConnections") or []:
        if isinstance(conn, dict):
            conn.pop("$$hashKey", None)
    return parsed


def _target(primary, secondary, target_route: str) -> list[Endpoint]:
    if target_route == PRIMARY:
        return primary
    if target_route == SECONDARY:
        return secondary
    raise ConnectionServiceError(f"Unknown target route {target_route!r}")


def _prepare(config: ConnectionConfig, client: AptentClient, target_route: str):
    """Compute and verify the write without sending it.

    Shared by preview and switch, so the diff shown to an engineer is
    produced by the same code path that performs the change.
    """
    (
        wrapper,
        cfg,
        live_type,
        strategy,
        isd,
        current,
        primary,
        secondary,
        route,
    ) = _resolve(config, client)

    if route == UNKNOWN:
        raise ConnectionServiceError(
            f"Current connection ({summarise(current)}) matches neither "
            f"configured route — refusing to switch until that is resolved."
        )
    if route == target_route:
        raise ConnectionServiceError(f"{config.institution_name} is already on {target_route}.")

    target = _target(primary, secondary, target_route)

    try:
        new_isd = apply_switch(isd, strategy, target)
        assert_only_connection_changed(isd, new_isd, strategy, target)
    except DiffAssertionError:
        raise
    except ConnectionSwitchError as exc:
        raise ConnectionServiceError(str(exc)) from exc

    service, path = endpoint_for(live_type, config.interchange_id)

    payload = dict(cfg)
    payload["interchangeSpecificData"] = new_isd
    payload["specificData"] = _specific_data(new_isd)

    changed_field = "remoteUrl" if strategy == REMOTE_URL else "sinkConnections"
    target_route_row = _route(config, target_route)

    return {
        "from_medium": _medium(config, route),
        "to_medium": _medium(config, target_route),
        "to_medium_note": target_route_row.medium_note if target_route_row else None,
        "to_medium_updated_at": (
            target_route_row.updated_at if target_route_row else None
        ),
        "wrapper": wrapper,
        "live_type": live_type,
        "strategy": strategy,
        "from_route": route,
        "to_route": target_route,
        "current": current,
        "target": target,
        "isd": isd,
        "new_isd": new_isd,
        "payload": payload,
        "service": service,
        "path": path,
        "changed_field": changed_field,
        "fields_untouched": max(len(cfg) - 1, 0),
    }


def preview_switch(
    db: Session, client: AptentClient, config_id: int, target_route: str
) -> dict:
    config = get_config(db, config_id)
    p = _prepare(config, client, target_route)

    return {
        "config_id": config.id,
        "institution_name": config.institution_name,
        "interchange_id": config.interchange_id,
        "interchange_type": p["live_type"],
        "strategy": p["strategy"],
        "from_route": p["from_route"],
        "to_route": p["to_route"],
        "from_medium": p["from_medium"],
        "from_medium_label": medium_label(p["from_medium"]),
        "to_medium": p["to_medium"],
        "to_medium_label": medium_label(p["to_medium"]),
        "to_medium_note": p["to_medium_note"],
        "to_medium_updated_at": p["to_medium_updated_at"],
        "changed_field": p["changed_field"],
        "before": summarise(p["current"]),
        "after": summarise(p["target"]),
        "target_service": p["service"],
        "target_path": p["path"],
        "fields_untouched": p["fields_untouched"],
        "switchable": True,
        "note": None,
    }


def execute_switch(
    db: Session,
    client: AptentClient,
    config_id: int,
    target_route: str,
    expected_from_route: str | None = None,
) -> dict:
    config = get_config(db, config_id)
    p = _prepare(config, client, target_route)

    # Optimistic concurrency: if Cosmos has moved since the preview, stop.
    if expected_from_route and p["from_route"] != expected_from_route:
        raise ConnectionServiceError(
            f"{config.institution_name} is now on {p['from_route']}, not "
            f"{expected_from_route}. Someone else may have switched it — "
            f"re-check before retrying."
        )

    before, after = summarise(p["current"]), summarise(p["target"])

    def _log(outcome: str, error: str | None = None) -> None:
        db.add(
            ConnectionSwitchLog(
                config_id=config.id,
                interchange_id=config.interchange_id,
                institution_name=config.institution_name,
                from_route=p["from_route"],
                to_route=target_route,
                from_medium=p["from_medium"],
                to_medium=p["to_medium"],
                from_value=before[:255],
                to_value=after[:255],
                outcome=outcome,
                error=(error[:500] if error else None),
            )
        )
        db.commit()

    try:
        client.update_interchange_sink(
            p["live_type"], config.interchange_id, p["payload"]
        )
    except Exception as exc:  # noqa: BLE001 - audit before re-raising
        _log("FAILED", str(exc))
        raise

    # Confirm by re-reading rather than trusting the 200.
    confirmed = False
    try:
        _, cfg2 = _find_live(client, config.interchange_id)
        isd2 = cfg2.get("interchangeSpecificData") or ""
        now = read_current(isd2, p["strategy"])
        confirmed = sorted(map(str, now)) == sorted(map(str, p["target"]))
    except Exception:  # noqa: BLE001 - a failed re-read is not a failed write
        confirmed = False

    outcome = "SUCCESS" if confirmed else "UNCONFIRMED"
    _log(outcome, None if confirmed else "Write accepted but re-read did not match")

    reconnect = (
        SOCKET_RECONNECT_SECONDS if p["strategy"] == SINK_CONNECTIONS else None
    )
    message = (
        f"{config.institution_name} switched to "
        f"{medium_label(p['to_medium'])} — {target_route} ({after})."
        if confirmed
        else (
            f"Write was accepted but re-reading Cosmos still does not show "
            f"{after}. Verify in the portal before assuming this took effect."
        )
    )
    if confirmed and reconnect:
        message += (
            f" Socket connections re-establish on a polling interval — allow "
            f"up to {reconnect}s."
        )

    return {
        "config_id": config.id,
        "institution_name": config.institution_name,
        "interchange_id": config.interchange_id,
        "from_route": p["from_route"],
        "to_route": target_route,
        "from_medium": p["from_medium"],
        "to_medium": p["to_medium"],
        "before": before,
        "after": after,
        "outcome": outcome,
        "confirmed": confirmed,
        "message": message,
        "reconnect_expected_seconds": reconnect,
    }


def switch_history(db: Session, config_id: int, limit: int = 50):
    return list(
        db.scalars(
            select(ConnectionSwitchLog)
            .where(ConnectionSwitchLog.config_id == config_id)
            .order_by(ConnectionSwitchLog.id.desc())
            .limit(limit)
        )
    )
