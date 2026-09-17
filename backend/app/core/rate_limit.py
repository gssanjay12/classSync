import time
from collections import defaultdict
from fastapi import HTTPException, Request, status

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        window_start = now - 60
        # Clean older requests
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        if len(self.requests[key]) >= self.requests_per_minute:
            return True
        self.requests[key].append(now)
        return False

# Limiters for sensitive flows
auth_limiter = RateLimiter(requests_per_minute=20)
general_limiter = RateLimiter(requests_per_minute=120)

def rate_limit_auth(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if auth_limiter.is_rate_limited(f"auth:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please wait a minute and try again."
        )
