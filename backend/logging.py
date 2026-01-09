from __future__ import annotations

from typing import Dict


def sanitize_log(event: Dict[str, str]) -> Dict[str, str]:
    sanitized = {}
    for key, value in event.items():
        if key in {"payload", "email"}:
            continue
        sanitized[key] = value
    return sanitized
