"""Transport boundary for Cosmos.

The router and orchestration layer depend only on the AptentClient Protocol,
so they stay testable against captured fixtures without reaching Cosmos.

Nothing in here may log or persist the payloads passing through — they carry
each institution's integration password, clientSecret, and a reference to its
Zone PIN Key. Use `scrub()` on anything that could reach a log or an error.
"""

import os
import threading
import time
from typing import Protocol, runtime_checkable

import httpx
from dotenv import load_dotenv

from app.services.connection_switch import endpoint_for

# This module reads its config lazily, so don't depend on some other import
# having loaded .env first.
load_dotenv()

# Hosts that follow the {key}.{APTENT_BASE_DOMAIN} pattern.
TOKEN_HOST = "aptent-cosmos"
INTERCHANGE_HOST = "card-transaction-routing-service"

TOKEN_PATH = "/oauth/token"
INTERCHANGE_PATH = "/interchange"

# Renew this many seconds before the token actually expires, so a request
# never races the boundary.
REFRESH_SKEW_SECONDS = 60

DEFAULT_TIMEOUT = 15.0

# Redacted in any log or error path.
SENSITIVE_KEYS = {
    "password",
    "clientsecret",
    "client_secret",
    "componentunderlmk",
    "keycheckvalue",
    "sourcezpk",
    "sinkzpk",
    "access_token",
    "authorization",
}


class AptentError(Exception):
    """Any failure talking to Cosmos."""


class AptentAuthError(AptentError):
    """Credentials were rejected, or no usable credential could be obtained.

    Kept distinct so the UI can say "Aptent rejected our credentials"
    instead of surfacing a generic failure during an incident.
    """


class AptentNotFound(AptentError):
    """The requested interchange is not present in Cosmos."""


def _oauth_error(resp) -> str:
    """Surface RFC 6749 error fields if present.

    `error` and `error_description` are diagnostic, not secret — they are
    the difference between "invalid_client" and a blind guess.
    """
    try:
        body = resp.json()
    except Exception:  # noqa: BLE001 - not JSON, nothing to add
        return ""
    if not isinstance(body, dict):
        return ""
    err = body.get("error")
    desc = body.get("error_description")
    if err and desc:
        return f": {err} — {desc}"
    if err:
        return f": {err}"
    return ""


def _unwrap_token_body(body, status_code: int) -> dict:
    """Return the dict holding access_token, whichever shape Cosmos used.

    Cosmos does not return the plain RFC 6749 body. It wraps it:

        {"success": true, "errors": [], "result": {"access_token": ...}}

    A bare OAuth2 body is still accepted, so this works against a standard
    Spring token endpoint too.
    """
    if not isinstance(body, dict):
        raise AptentAuthError(
            f"Aptent token response (HTTP {status_code}) was "
            f"{type(body).__name__}, expected an object"
        )

    if "access_token" in body:
        return body

    if isinstance(body.get("result"), dict) and "access_token" in body["result"]:
        # Envelope present and populated — but still honour an explicit
        # failure flag rather than using a token from a failed response.
        if body.get("success") is False:
            raise AptentAuthError(
                f"Aptent reported failure minting a token: "
                f"{body.get('errors') or 'no detail given'}"
            )
        return body["result"]

    if body.get("success") is False or body.get("errors"):
        raise AptentAuthError(
            f"Aptent rejected the token request: "
            f"{body.get('errors') or 'no detail given'}"
        )

    # Key names only — values could carry a token.
    inner = (
        f"; result fields: {sorted(body['result'])}"
        if isinstance(body.get("result"), dict)
        else ""
    )
    raise AptentAuthError(
        f"Aptent token response (HTTP {status_code}) had no access_token. "
        f"Fields present: {sorted(body)}{inner}"
    )


def scrub(value):
    """Recursively redact credential-bearing keys before logging."""
    if isinstance(value, dict):
        return {
            k: ("***" if k.lower() in SENSITIVE_KEYS else scrub(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


@runtime_checkable
class AptentClient(Protocol):
    """Minimum surface the connection switcher needs."""

    def fetch_interchanges(self) -> list[dict]:
        """Return the raw list from GET /interchange.

        Each element is the wrapper Cosmos sends: ``{"config": {...},
        "running": bool, "traced": bool, "filterMode": ...}``.
        """
        ...

    def update_interchange_sink(
        self, type_name: str, interchange_id: int, payload: dict
    ) -> dict:
        """POST the full interchange object to the edit-sink endpoint for
        this interchange type."""
        ...

    def auth_status(self) -> dict:
        """Diagnostic: is our credential working, and when did it last work."""
        ...


class AptentHttpClient:
    """Talks to Cosmos with an OAuth2 client_credentials token.

    The token is minted once, cached in memory, and renewed shortly before
    it expires. A 401 mid-flight invalidates the cache and retries once, so
    a revoked or rotated credential recovers without a restart.
    """

    def __init__(
        self,
        base_domain: str,
        client_id: str,
        client_secret: str,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
        host_overrides: dict[str, str] | None = None,
    ):
        self._base_domain = base_domain.strip().strip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._timeout = timeout
        self._transport = transport
        # For cluster-internal DNS, which does not follow {key}.{domain}.
        self._host_overrides = host_overrides or {}

        self._lock = threading.Lock()
        self._token: str | None = None
        self._expires_at: float = 0.0

        self._last_success: float | None = None
        self._last_error: str | None = None

    # --- url building ------------------------------------------------------

    def _base_url(self, host_key: str) -> str:
        if host_key in self._host_overrides:
            return self._host_overrides[host_key].rstrip("/")
        return f"https://{host_key}.{self._base_domain}"

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self._timeout, transport=self._transport)

    # --- token -------------------------------------------------------------

    def _mint_token(self) -> tuple[str, float]:
        """Exchange client credentials for an access token."""
        url = f"{self._base_url(TOKEN_HOST)}{TOKEN_PATH}"
        try:
            with self._client() as http:
                resp = http.post(
                    url,
                    headers={"Accept": "application/json"},
                    data={"grant_type": "client_credentials"},
                    auth=(self._client_id, self._client_secret),
                )
        except httpx.HTTPError as exc:
            raise AptentAuthError(
                f"Could not reach the Aptent token endpoint: {exc}"
            ) from exc

        if resp.status_code in (400, 401, 403):
            raise AptentAuthError(
                f"Aptent rejected client '{self._client_id}' "
                f"(HTTP {resp.status_code}){_oauth_error(resp)}. Check "
                f"APTENT_CLIENT_ID / APTENT_CLIENT_SECRET."
            )

        # 3xx is a failure here, not a success. Spring redirects the token
        # endpoint to its login page when it does not accept the client
        # credentials, and httpx does not follow redirects — so without this
        # a 302 would fall through and fail later as "no access_token".
        if 300 <= resp.status_code < 400:
            location = resp.headers.get("location", "")
            hint = " (redirected to a login page — client auth was not accepted)"
            if location and "login" not in location.lower():
                hint = f" (redirected to {location.split('?')[0]})"
            raise AptentAuthError(
                f"Aptent token endpoint returned HTTP {resp.status_code}{hint}. "
                f"Check APTENT_CLIENT_ID / APTENT_CLIENT_SECRET."
            )

        if resp.status_code >= 400:
            raise AptentAuthError(
                f"Aptent token endpoint returned HTTP {resp.status_code}"
                f"{_oauth_error(resp)}"
            )

        try:
            body = resp.json()
        except Exception as exc:  # noqa: BLE001 - not JSON at all
            ctype = resp.headers.get("content-type", "unknown")
            raise AptentAuthError(
                f"Aptent token endpoint returned HTTP {resp.status_code} with "
                f"a non-JSON body (content-type: {ctype}). This usually means "
                f"the request did not reach the token endpoint."
            ) from exc

        body = _unwrap_token_body(body, resp.status_code)
        token = body["access_token"]

        # expires_in is seconds. Fall back to a short life if absent so we
        # re-mint often rather than clinging to a token of unknown age.
        expires_in = int(body.get("expires_in") or 300)
        return token, time.monotonic() + max(expires_in - REFRESH_SKEW_SECONDS, 30)

    def _get_token(self, force: bool = False) -> str:
        with self._lock:
            if force:
                self._token = None
            if self._token and time.monotonic() < self._expires_at:
                return self._token
            # Only one thread mints; the rest wait and reuse the result.
            token, expires_at = self._mint_token()
            self._token, self._expires_at = token, expires_at
            return token

    # --- requests ----------------------------------------------------------

    def _request(self, method: str, url: str, *, json_body=None, retries: int = 0):
        """Issue an authenticated request, re-minting once on a 401.

        `retries` applies only to transport errors on reads. A write is never
        retried — a duplicate edit-sink POST could re-apply a change.
        """
        attempt = 0
        while True:
            token = self._get_token()
            try:
                with self._client() as http:
                    resp = http.request(
                        method,
                        url,
                        headers={
                            "Accept": "application/json",
                            "Authorization": f"Bearer {token}",
                        },
                        json=json_body,
                    )
            except httpx.HTTPError as exc:
                if attempt < retries:
                    attempt += 1
                    continue
                self._last_error = str(exc)
                raise AptentError(f"Request to Cosmos failed: {exc}") from exc

            if resp.status_code == 401:
                # Token rejected: mint a fresh one and try exactly once more.
                if attempt == 0:
                    attempt = max(attempt, 1)
                    self._get_token(force=True)
                    continue
                self._last_error = "401 from Cosmos after refreshing the token"
                raise AptentAuthError(
                    "Aptent rejected our token twice. The client may have been "
                    "revoked or lost its authorities."
                )

            if resp.status_code == 403:
                self._last_error = f"403 from {url}"
                raise AptentAuthError(
                    f"Aptent returned 403. Client '{self._client_id}' may be "
                    f"missing the aptent_edit_interchanges authority."
                )

            if resp.status_code == 404:
                self._last_error = f"404 from {url}"
                raise AptentNotFound(f"Cosmos returned 404 for {url}")

            if resp.status_code >= 400:
                self._last_error = f"HTTP {resp.status_code} from {url}"
                raise AptentError(
                    f"Cosmos returned HTTP {resp.status_code} for {url}"
                )

            self._last_success = time.time()
            self._last_error = None
            return resp

    # --- protocol ----------------------------------------------------------

    def fetch_interchanges(self) -> list[dict]:
        url = f"{self._base_url(INTERCHANGE_HOST)}{INTERCHANGE_PATH}"
        # Safe to retry: a read has no side effects.
        resp = self._request("GET", url, retries=1)
        data = resp.json()
        if not isinstance(data, list):
            raise AptentError("Expected a list of interchanges from Cosmos")
        return data

    def update_interchange_sink(
        self, type_name: str, interchange_id: int, payload: dict
    ) -> dict:
        # Raises on an unmapped interchange type rather than guessing a host.
        host_key, path = endpoint_for(type_name, interchange_id)
        url = f"{self._base_url(host_key)}{path}"
        # retries=0: never re-send a write.
        resp = self._request("POST", url, json_body=payload, retries=0)
        try:
            return resp.json()
        except Exception:  # noqa: BLE001 - some services return an empty body
            return {}

    def auth_status(self) -> dict:
        with self._lock:
            has_token = bool(self._token) and time.monotonic() < self._expires_at
            expires_in = (
                max(int(self._expires_at - time.monotonic()), 0) if has_token else None
            )
        return {
            "configured": True,
            "client_id": self._client_id,
            "base_domain": self._base_domain,
            "has_cached_token": has_token,
            "token_expires_in_seconds": expires_in,
            "last_success_at": self._last_success,
            "last_error": self._last_error,
        }


class UnconfiguredAptentClient:
    """Used when APTENT_* env vars are absent.

    Fails loudly rather than silently returning nothing, so a half-wired
    deployment is obvious at the first request instead of looking like an
    empty estate.
    """

    MESSAGE = (
        "Aptent client is not configured. Set APTENT_BASE_DOMAIN, "
        "APTENT_CLIENT_ID and APTENT_CLIENT_SECRET."
    )

    def fetch_interchanges(self) -> list[dict]:
        raise AptentAuthError(self.MESSAGE)

    def update_interchange_sink(
        self, type_name: str, interchange_id: int, payload: dict
    ) -> dict:
        raise AptentAuthError(self.MESSAGE)

    def auth_status(self) -> dict:
        return {
            "configured": False,
            "client_id": None,
            "base_domain": None,
            "has_cached_token": False,
            "token_expires_in_seconds": None,
            "last_success_at": None,
            "last_error": self.MESSAGE,
        }


def _host_overrides_from_env() -> dict[str, str]:
    """APTENT_HOST_<KEY>=https://... for cluster-internal DNS, which does not
    follow the {key}.{domain} pattern. Key is upper-snake, e.g.
    APTENT_HOST_BANK_CASHOUT_SERVICE.
    """
    overrides = {}
    for name, value in os.environ.items():
        if name.startswith("APTENT_HOST_") and value.strip():
            key = name[len("APTENT_HOST_") :].lower().replace("_", "-")
            overrides[key] = value.strip()
    return overrides


# Built once per process; the token cache lives on the instance.
_client_singleton: AptentClient | None = None
_singleton_lock = threading.Lock()


def build_aptent_client() -> AptentClient:
    domain = os.getenv("APTENT_BASE_DOMAIN", "").strip()
    client_id = os.getenv("APTENT_CLIENT_ID", "").strip()
    client_secret = os.getenv("APTENT_CLIENT_SECRET", "").strip()

    if not (domain and client_id and client_secret):
        return UnconfiguredAptentClient()

    return AptentHttpClient(
        base_domain=domain,
        client_id=client_id,
        client_secret=client_secret,
        timeout=float(os.getenv("APTENT_TIMEOUT_SECONDS", DEFAULT_TIMEOUT)),
        host_overrides=_host_overrides_from_env(),
    )


def get_aptent_client() -> AptentClient:
    """FastAPI dependency. Overridden in tests."""
    global _client_singleton
    if _client_singleton is None:
        with _singleton_lock:
            if _client_singleton is None:
                client = build_aptent_client()
                # Deliberately don't cache the unconfigured placeholder. If
                # it were cached, a process that served one request before
                # the credentials were present would keep reporting
                # "not configured" for its whole life.
                if isinstance(client, UnconfiguredAptentClient):
                    return client
                _client_singleton = client
    return _client_singleton


def reset_aptent_client() -> None:
    """Drop the cached singleton — used by tests and after config changes."""
    global _client_singleton
    _client_singleton = None
