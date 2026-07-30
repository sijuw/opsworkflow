"""Pure switch logic for the Switch Institution Connection.

No HTTP, no database, no logging. Everything here is a function from
strings to strings, which is what makes it testable against captured
fixtures without touching Cosmos.

The governing rule: `interchangeSpecificData` is treated as *text*, never
as data. It is never parsed and re-serialised, because that would reorder
keys, change escaping, and drop the AngularJS `$$hashKey` artifacts that
Cosmos has persisted. Instead we replace the smallest possible substring
and then prove nothing else moved.

That matters because the payload also carries the institution's integration
password, its clientSecret, and a reference to its Zone PIN Key. A switch
must not be able to disturb any of them.
"""

import json
import re
from dataclasses import dataclass

# Strategy names
REMOTE_URL = "REMOTE_URL"
SINK_CONNECTIONS = "SINK_CONNECTIONS"

# Route names. Deliberately carry no implied medium: for most institutions
# PRIMARY is a GCP VPN, but for NIBSS it is a leased line. Always display the
# medium alongside the route name.
PRIMARY = "PRIMARY"
SECONDARY = "SECONDARY"
UNKNOWN = "UNKNOWN"

# What a route physically runs over. Human-maintained: OpsFlow cannot verify
# that a port actually egresses via GCP, so treat these as "as configured"
# and surface how recently they were confirmed.
MEDIUM_LABELS = {
    "VPN_GCP": "VPN (GCP)",
    "VPN_AWS": "VPN (AWS)",
    "LEASED_LINE": "Leased line",
    "OTHER": "Other",
}
MEDIUMS = tuple(MEDIUM_LABELS)


def medium_label(medium: str | None) -> str:
    if not medium:
        return "unspecified"
    return MEDIUM_LABELS.get(medium, medium)

MIN_PORT = 1
MAX_PORT = 65535

# typeName (lowercased) -> switch strategy. REST interchanges are switched
# on remoteUrl even when they also carry sinkConnections (UBA DCIR,
# UBADCIR_TEAMAPT, MPG all have both populated).
STRATEGY_BY_TYPE = {
    "rest_interchange": REMOTE_URL,
    "bankcashoutpostbridge": SINK_CONNECTIONS,
    "uppostbridge": SINK_CONNECTIONS,
    "postbridge": SINK_CONNECTIONS,
    "coralpaypostbridge": SINK_CONNECTIONS,
    "postbridgenotification": SINK_CONNECTIONS,
}

# typeName (lowercased) -> (service host key, edit path template)
ENDPOINT_BY_TYPE = {
    "rest_interchange": ("aptent-rest", "/rest-service/interchange/edit-sink/{id}"),
    "bankcashoutpostbridge": (
        "bank-cashout-service",
        "/postbridge-service/edit-sink/{id}",
    ),
    "uppostbridge": ("up-cashout-service", "/postbridge-service/edit-sink/{id}"),
    "postbridge": ("postbridge-service", "/postbridge-service/edit-sink/{id}"),
    "coralpaypostbridge": (
        "coralpay-cashout-service",
        "/postbridge-service/edit-sink/{id}",
    ),
}


class ConnectionSwitchError(Exception):
    """Raised when a switch cannot be performed safely."""


class DiffAssertionError(ConnectionSwitchError):
    """The edit changed something other than the intended connection."""


@dataclass(frozen=True)
class Endpoint:
    """One connection. host is None for REST, meaning 'keep the live host'."""

    host: str | None
    port: int

    def __str__(self) -> str:
        return f"{self.host}:{self.port}" if self.host else str(self.port)


# --- type dispatch ---------------------------------------------------------


def normalise_type(type_name: str | None) -> str:
    return (type_name or "").strip().lower()


def strategy_for(type_name: str | None) -> str:
    """Which field this interchange switches on.

    Fails closed: an unrecognised type is never guessed at, because posting
    an institution's configuration to the wrong service is not a recoverable error.
    """
    key = normalise_type(type_name)
    if key not in STRATEGY_BY_TYPE:
        raise ConnectionSwitchError(
            f"Unknown interchange type {type_name!r} — refusing to switch. "
            f"Known types: {', '.join(sorted(STRATEGY_BY_TYPE))}"
        )
    return STRATEGY_BY_TYPE[key]


def endpoint_for(type_name: str | None, interchange_id: int) -> tuple[str, str]:
    key = normalise_type(type_name)
    if key not in ENDPOINT_BY_TYPE:
        raise ConnectionSwitchError(
            f"No edit-sink endpoint mapped for interchange type {type_name!r} "
            f"— refusing to switch."
        )
    host_key, path = ENDPOINT_BY_TYPE[key]
    return host_key, path.format(id=interchange_id)


def validate_port(port: int) -> int:
    """Reject anything outside the valid TCP range.

    Cosmos itself does not validate this — a five-digit port was accepted
    and persisted during manual editing.
    """
    if not isinstance(port, int) or isinstance(port, bool):
        raise ConnectionSwitchError(f"Port must be an integer, got {port!r}")
    if not (MIN_PORT <= port <= MAX_PORT):
        raise ConnectionSwitchError(
            f"Port {port} is outside the valid range {MIN_PORT}-{MAX_PORT}"
        )
    return port


# --- reading current state -------------------------------------------------

_REMOTE_URL_RE = re.compile(
    r'("remoteUrl"\s*:\s*"[a-zA-Z][a-zA-Z0-9+.\-]*://[^:"/]+:)(\d+)(/)'
)


def read_remote_url_port(isd: str) -> int | None:
    m = _REMOTE_URL_RE.search(isd)
    return int(m.group(2)) if m else None


def read_sink_connections(isd: str) -> list[Endpoint]:
    """Read the connection list. Parsing is fine for *reading* — it's only
    writing that must avoid re-serialisation."""
    try:
        inner = json.loads(isd)
    except (TypeError, ValueError):
        return []
    out = []
    for conn in inner.get("sinkConnections") or []:
        host, port = conn.get("host"), conn.get("port")
        if host is None or port in (None, ""):
            continue
        try:
            out.append(Endpoint(host=str(host), port=int(port)))
        except (TypeError, ValueError):
            continue
    return out


def read_current(isd: str, strategy: str) -> list[Endpoint]:
    if strategy == REMOTE_URL:
        port = read_remote_url_port(isd)
        return [Endpoint(host=None, port=port)] if port is not None else []
    return read_sink_connections(isd)


def identify_route(
    current: list[Endpoint],
    primary: list[Endpoint],
    secondary: list[Endpoint],
) -> str:
    """Match the live connections against the two configured routes.

    Returns UNKNOWN when it matches neither. UNKNOWN must disable switching
    rather than being coerced into a guess — that is the state the invalid
    port 95677 produced.
    """
    if not current:
        return UNKNOWN
    if _same(current, primary):
        return PRIMARY
    if _same(current, secondary):
        return SECONDARY
    return UNKNOWN


def _same(a: list[Endpoint], b: list[Endpoint]) -> bool:
    if not a or not b or len(a) != len(b):
        return False
    # Order-insensitive: Cosmos does not guarantee connection ordering.
    return sorted(map(str, a)) == sorted(map(str, b))


# --- writing: surgical substring replacement -------------------------------


def swap_remote_url_port(isd: str, new_port: int, validate: bool = True) -> str:
    """Replace only the port digits inside remoteUrl. Host is untouched.

    validate=False is used only when reconstructing a previously-live value
    during verification — the current config may legitimately hold an
    invalid port (Cosmos does not validate), and we must be able to
    reproduce it to prove we changed nothing else.
    """
    if validate:
        validate_port(new_port)
    matches = _REMOTE_URL_RE.findall(isd)
    if not matches:
        raise ConnectionSwitchError("No remoteUrl found in interchangeSpecificData")
    if len(matches) > 1:
        raise ConnectionSwitchError(
            f"Expected one remoteUrl, found {len(matches)} — refusing to switch"
        )
    return _REMOTE_URL_RE.sub(lambda m: f"{m.group(1)}{new_port}{m.group(3)}", isd, count=1)


_SINK_ARRAY_RE = re.compile(r'("sinkConnections"\s*:\s*)(\[.*?\])(\s*[,}])', re.DOTALL)


def swap_sink_connections(
    isd: str, endpoints: list[Endpoint], validate: bool = True
) -> str:
    """Replace the whole sinkConnections array with the target route.

    The connection count is preserved by construction: whatever list is
    passed in is what gets written. A three-socket pool switched to a
    three-entry route stays three sockets.

    Note: the written entries carry only host and port. Cosmos round-trips
    an AngularJS "$$hashKey" on existing entries; we deliberately do not
    reproduce it, because it is client-side rendering state with no meaning
    to the server and no sensible value for a newly written connection.
    """
    if not endpoints:
        raise ConnectionSwitchError("Refusing to write an empty connection list")
    for ep in endpoints:
        if validate:
            validate_port(ep.port)
        if not ep.host:
            raise ConnectionSwitchError(
                f"Socket connections require a host; got {ep!r}"
            )

    m = _SINK_ARRAY_RE.search(isd)
    if not m:
        raise ConnectionSwitchError("No sinkConnections array found in interchangeSpecificData")

    # Match the escaping style Cosmos uses: compact, no spaces.
    rendered = json.dumps(
        [{"host": ep.host, "port": str(ep.port)} for ep in endpoints],
        separators=(",", ":"),
    )
    return isd[: m.start(2)] + rendered + isd[m.end(2) :]


def apply_switch(
    isd: str, strategy: str, endpoints: list[Endpoint], validate: bool = True
) -> str:
    if strategy == REMOTE_URL:
        if len(endpoints) != 1:
            raise ConnectionSwitchError(
                f"REST interchanges take exactly one endpoint, got {len(endpoints)}"
            )
        return swap_remote_url_port(isd, endpoints[0].port, validate=validate)
    return swap_sink_connections(isd, endpoints, validate=validate)


# --- the safety rail -------------------------------------------------------


def assert_only_connection_changed(
    before: str, after: str, strategy: str, intended: list[Endpoint]
) -> None:
    """Prove the edit touched nothing but the connection.

    The invariant differs by strategy, because the two edits have different
    shapes:

    * REMOTE_URL replaces a few digits in place, so we reverse our own
      change and require byte-identity with what Cosmos returned.
    * SINK_CONNECTIONS replaces a whole array by design, so reversal cannot
      reproduce the original bytes. Instead we require every byte *outside*
      the array to be unchanged, and the array itself to contain exactly
      the endpoints we meant to write.

    Either way, a password, timeout or key reference that moved will fail
    the check and nothing is sent.
    """
    if before == after:
        raise DiffAssertionError("Edit produced no change")

    if strategy == REMOTE_URL:
        _assert_remote_url_swap(before, after)
    else:
        _assert_sink_swap(before, after, intended)


def _assert_remote_url_swap(before: str, after: str) -> None:
    original_port = read_remote_url_port(before)
    if original_port is None:
        raise DiffAssertionError("No remoteUrl in the original — cannot verify")

    try:
        # validate=False: the live value may itself be an invalid port and
        # we still have to reproduce it exactly.
        reversed_ = swap_remote_url_port(after, original_port, validate=False)
    except ConnectionSwitchError as exc:
        raise DiffAssertionError(f"Could not reverse the edit to verify it: {exc}")

    if reversed_ != before:
        raise DiffAssertionError(
            "Edit changed more than the connection — aborting. "
            f"({_first_difference(before, reversed_)})"
        )


def _assert_sink_swap(before: str, after: str, intended: list[Endpoint]) -> None:
    mb = _SINK_ARRAY_RE.search(before)
    ma = _SINK_ARRAY_RE.search(after)
    if not mb or not ma:
        raise DiffAssertionError(
            "sinkConnections array missing from one side — cannot verify"
        )

    if before[: mb.start(2)] != after[: ma.start(2)]:
        raise DiffAssertionError(
            "Edit changed more than the connection — aborting. "
            f"({_first_difference(before[: mb.start(2)], after[: ma.start(2)])})"
        )
    if before[mb.end(2) :] != after[ma.end(2) :]:
        raise DiffAssertionError(
            "Edit changed more than the connection — aborting. "
            f"({_first_difference(before[mb.end(2) :], after[ma.end(2) :])})"
        )

    written = read_sink_connections(after)
    if sorted(map(str, written)) != sorted(map(str, intended)):
        raise DiffAssertionError(
            f"Written connections {summarise(written)} do not match the "
            f"intended route {summarise(intended)} — aborting"
        )
    if len(written) != len(intended):
        raise DiffAssertionError(
            f"Connection count changed: wrote {len(written)}, intended "
            f"{len(intended)} — aborting"
        )


def _first_difference(a: str, b: str) -> str:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return f"first divergence at offset {i}: {a[max(0,i-25):i+25]!r} vs {b[max(0,i-25):i+25]!r}"
    return f"lengths differ: {len(a)} vs {len(b)}"


def summarise(endpoints: list[Endpoint]) -> str:
    """Short human-readable form for the audit log and the preview dialog."""
    return ", ".join(str(e) for e in endpoints) if endpoints else "(none)"
