from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ConnectionConfig(Base):
    """One row per institution OpsFlow can switch.

    Deliberately holds no interchange configuration — Cosmos is the source
    of truth. This is only the note: "for this institution, the candidate
    routes are these." The live config is fetched fresh on every read and
    write.
    """

    __tablename__ = "connection_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    institution_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Cosmos interchange id; unique so we can't register the same one twice.
    interchange_id: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True, index=True
    )

    # typeName as Cosmos reports it (e.g. "rest_interchange",
    # "bankcashoutpostbridge"). Drives both the switch strategy and the
    # edit-sink endpoint. Stored case-normalised (lowercased) on write.
    interchange_type: Mapped[str] = mapped_column(String(60), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="1"
    )

    # Optional link to the email-module institution, for later joining.
    institution_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("institutions.id"), nullable=True
    )

    routes: Mapped[list["ConnectionRoute"]] = relationship(
        back_populates="config",
        cascade="all, delete-orphan",
        order_by="ConnectionRoute.name",
    )


class ConnectionRoute(Base):
    """One candidate route for an institution, e.g. PRIMARY.

    `medium` is what the route physically runs over. It matters because the
    route *name* carries no consistent meaning across institutions: for most
    banks PRIMARY is a GCP VPN, but for NIBSS it is a leased line. Anyone
    switching needs to see the medium, not just the label.

    It is human-maintained metadata — OpsFlow cannot verify that a given
    port actually egresses via GCP — so `updated_at` is exposed to let the
    UI show how long ago someone last confirmed it.
    """

    __tablename__ = "connection_routes"
    __table_args__ = (
        UniqueConstraint(
            "config_id", "name", name="uq_connection_routes_config_name"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("connection_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # "PRIMARY" or "SECONDARY". A string rather than an enum so a future
    # third route needs no migration.
    name: Mapped[str] = mapped_column(String(20), nullable=False)

    # VPN_GCP | VPN_AWS | LEASED_LINE | OTHER. Required: a blank medium
    # defeats the purpose of recording it.
    medium: Mapped[str] = mapped_column(String(30), nullable=False)

    # Free text for the long tail, e.g. "tunnel B, reprovisioned May 2026".
    medium_note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    config: Mapped["ConnectionConfig"] = relationship(back_populates="routes")

    endpoints: Mapped[list["ConnectionRouteEndpoint"]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="ConnectionRouteEndpoint.sort_order",
    )


class ConnectionRouteEndpoint(Base):
    """One connection within a route.

    A route is a list of these: a single-connection institution has one row,
    Interswitch QT has three. Switching replaces the whole live connection
    list with the rows for the target route, preserving count.

    For REST interchanges host is NULL — meaning "keep the host Cosmos
    already has, change only the port".
    """

    __tablename__ = "connection_route_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    route_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("connection_routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    host: Mapped[str | None] = mapped_column(String(64), nullable=True)
    port: Mapped[int] = mapped_column(Integer, nullable=False)

    # Preserves connection ordering within a route (matters for pools).
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    route: Mapped["ConnectionRoute"] = relationship(back_populates="endpoints")


class ConnectionSwitchLog(Base):
    """Audit trail: which institution moved between which routes, over which
    medium, and whether it worked. There is no record of this action anywhere
    else, since the change lands in Cosmos, not in a table OpsFlow owns.
    """

    __tablename__ = "connection_switch_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    config_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("connection_configs.id"), nullable=True
    )
    interchange_id: Mapped[int] = mapped_column(Integer, nullable=False)
    institution_name: Mapped[str] = mapped_column(String(100), nullable=False)

    from_route: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_route: Mapped[str] = mapped_column(String(20), nullable=False)

    # Recorded so history reads "LEASED_LINE -> VPN_AWS" rather than only
    # port numbers, which is what a post-incident review actually needs.
    from_medium: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_medium: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Human-readable before/after (the port, or host:port list). Never the
    # full interchange payload — that carries credentials and key data.
    from_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # "SUCCESS" | "FAILED" | "UNCONFIRMED"
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
