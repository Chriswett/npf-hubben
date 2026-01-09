from __future__ import annotations

import os
import socket


def _check_postgres_connection() -> None:
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    timeout = float(os.environ.get("POSTGRES_TIMEOUT", "2.0"))
    with socket.create_connection((host, port), timeout=timeout):
        return


def run_migrations() -> None:
    _check_postgres_connection()


if __name__ == "__main__":
    run_migrations()
