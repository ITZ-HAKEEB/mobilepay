"""Small process-local limiter for starter deployments.

For multiple workers/instances, replace this with Redis-backed limiting.
Do not rely on this in-memory limiter as the only production fraud control.
"""
import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request

_hits: dict[str, deque] = defaultdict(deque)

def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    async def dependency(request: Request):
        forwarded = request.headers.get("x-forwarded-for", "")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else "unknown"
        )
        key = f"{request.url.path}:{client_ip}"
        now = time.monotonic()
        queue = _hits[key]
        while queue and queue[0] < now - window_seconds:
            queue.popleft()
        if len(queue) >= max_requests:
            raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
        queue.append(now)
    return dependency
