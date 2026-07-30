from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Kept in step with MEDIUM_LABELS in app.services.connection_switch.
Medium = Literal["VPN_GCP", "VPN_AWS", "LEASED_LINE", "OTHER"]


class EndpointIn(BaseModel):
    """One connection in a route.

    host is optional: for REST interchanges it is left unset, meaning
    "keep whatever host Cosmos already has and change only the port".
    """

    host: str | None = None
    port: int = Field(ge=1, le=65535)


class EndpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    host: str | None = None
    port: int


class RouteIn(BaseModel):
    """A candidate route: what it runs over, and where it points."""

    # Required — a blank medium defeats the point of recording it.
    medium: Medium
    medium_note: str | None = Field(default=None, max_length=255)
    endpoints: list[EndpointIn] = Field(min_length=1)


class RouteOut(BaseModel):
    medium: str
    medium_label: str
    medium_note: str | None = None
    # When the medium was last confirmed, so the UI can flag stale metadata.
    medium_updated_at: datetime | None = None
    endpoints: list[EndpointOut]


class ConnectionConfigCreate(BaseModel):
    institution_name: str = Field(min_length=1, max_length=100)
    interchange_id: int
    interchange_type: str = Field(min_length=1, max_length=60)
    institution_id: int | None = None
    is_active: bool = True

    primary: RouteIn
    secondary: RouteIn


class ConnectionConfigUpdate(BaseModel):
    institution_name: str | None = Field(default=None, min_length=1, max_length=100)
    interchange_type: str | None = Field(default=None, min_length=1, max_length=60)
    institution_id: int | None = None
    is_active: bool | None = None

    primary: RouteIn | None = None
    secondary: RouteIn | None = None


class ConnectionConfigResponse(BaseModel):
    id: int
    institution_name: str
    interchange_id: int
    interchange_type: str
    institution_id: int | None
    is_active: bool

    strategy: str
    primary: RouteOut
    secondary: RouteOut


class ConnectionStatusResponse(BaseModel):
    config_id: int
    institution_name: str
    interchange_id: int
    interchange_type: str
    strategy: str

    # PRIMARY | SECONDARY | UNKNOWN
    active_route: str
    # Medium of the live route; null when active_route is UNKNOWN.
    active_medium: str | None = None
    active_medium_label: str | None = None

    current: list[EndpointOut]
    current_summary: str

    primary: RouteOut
    secondary: RouteOut

    # Cosmos' own view of whether the interchange is up
    running: bool | None = None

    # False when active_route is UNKNOWN — the UI must not offer a switch
    switchable: bool
    note: str | None = None


class ConnectionSwitchRequest(BaseModel):
    config_id: int
    target_route: str = Field(pattern="^(PRIMARY|SECONDARY)$")

    # Optional optimistic-concurrency guard: the route the caller believed
    # was live when they previewed. If Cosmos has moved on, we abort.
    expected_from_route: str | None = Field(
        default=None, pattern="^(PRIMARY|SECONDARY|UNKNOWN)$"
    )


class ConnectionSwitchPreviewResponse(BaseModel):
    config_id: int
    institution_name: str
    interchange_id: int
    interchange_type: str
    strategy: str

    from_route: str
    to_route: str

    # The medium transition is the headline: "Leased line -> VPN (AWS)" tells
    # an engineer what they are actually doing; route names alone do not.
    from_medium: str
    from_medium_label: str
    to_medium: str
    to_medium_label: str
    to_medium_note: str | None = None
    to_medium_updated_at: datetime | None = None

    changed_field: str
    before: str
    after: str

    # Where the write would go, so the dialog can show it
    target_service: str
    target_path: str

    fields_untouched: int
    switchable: bool
    note: str | None = None


class ConnectionSwitchResponse(BaseModel):
    config_id: int
    institution_name: str
    interchange_id: int

    from_route: str
    to_route: str
    from_medium: str | None = None
    to_medium: str | None = None
    before: str
    after: str

    # SUCCESS | UNCONFIRMED
    outcome: str
    confirmed: bool
    message: str

    # Socket interchanges re-establish on a polling interval, so a
    # confirmed config change is not yet a moved connection.
    reconnect_expected_seconds: int | None = None


class ConnectionSwitchLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interchange_id: int
    institution_name: str
    from_route: str | None
    to_route: str
    from_medium: str | None
    to_medium: str | None
    from_value: str | None
    to_value: str | None
    outcome: str
    error: str | None
    created_at: datetime
