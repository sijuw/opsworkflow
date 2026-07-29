import os

from sqlalchemy import URL


def build_mysql_url(prefix: str) -> URL:
    """Build a MySQL URL from <prefix>_USER/_PASSWORD/_HOST/_PORT/_NAME.

    URL.create escapes each component, so credentials containing @ : / ? #
    survive intact. Interpolating them into an f-string does not: an "@" in
    the password terminates the credentials early and the remainder is
    parsed as part of the hostname.
    """
    port = os.getenv(f"{prefix}_PORT")

    return URL.create(
        drivername="mysql+pymysql",
        username=os.getenv(f"{prefix}_USER"),
        password=os.getenv(f"{prefix}_PASSWORD"),
        host=os.getenv(f"{prefix}_HOST"),
        port=int(port) if port else None,
        database=os.getenv(f"{prefix}_NAME"),
    )
