import os
import secrets

from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()


def require_api_token(authorization: str = Header(default="")) -> None:
    """Guard endpoints behind a shared bearer token.

    Refuses every request when API_TOKEN is unset rather than defaulting
    to open — an unconfigured deployment should fail closed, not silently
    serve /email/send to anyone who can reach the port.
    """
    # Read per-request rather than at import: this module is imported
    # before app.db.database, so an import-time read would run ahead of
    # whichever load_dotenv() happens to fire first.
    expected = os.getenv("API_TOKEN")

    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_TOKEN is not configured on the server",
        )

    scheme, _, token = authorization.partition(" ")

    # compare_digest keeps the check constant-time
    if scheme.lower() != "bearer" or not secrets.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
