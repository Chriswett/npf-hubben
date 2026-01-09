from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .domain import RateLimitError, UnauthorizedError, User


@dataclass
class RateLimiter:
    max_attempts: int = 5
    attempts: Dict[str, int] = field(default_factory=dict)

    def register_attempt(self, key: str) -> None:
        count = self.attempts.get(key, 0) + 1
        self.attempts[key] = count
        if count > self.max_attempts:
            raise RateLimitError("rate_limit_exceeded")


def require_role(user: Optional[User], allowed: List[str]) -> None:
    if user is None or user.role not in allowed:
        raise UnauthorizedError("unauthorized")
