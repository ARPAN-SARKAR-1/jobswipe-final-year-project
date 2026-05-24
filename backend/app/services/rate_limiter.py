from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request, status

RATE_LIMIT_MESSAGE = "Too many attempts. Please try again later."


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, max_attempts: int, window_seconds: int) -> None:
        now = monotonic()
        cutoff = now - window_seconds
        events = self._events[key]
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= max_attempts:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=RATE_LIMIT_MESSAGE)
        events.append(now)


rate_limiter = InMemoryRateLimiter()


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_key(prefix: str, request: Request, identifier: str | int | None = None) -> str:
    normalized_identifier = str(identifier or "anonymous").strip().lower()
    return f"{prefix}:{client_ip(request)}:{normalized_identifier}"
