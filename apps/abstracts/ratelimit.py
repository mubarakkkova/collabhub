from typing import Any, Callable

from functools import wraps

from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_429_TOO_MANY_REQUESTS
from django.core.cache import cache

from django.utils.translation import gettext as _

KEY_PREFIX = "ratelimit"
SCOPES = ("user", "ip", "user_or_ip")
PERIODS = {"second": 1 , "minute": 60,}


def get_client_ip(request: DRFRequest) -> str:
    """Return the IP address of the client."""
    forwarded_for: str = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for: 
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")

def get_client_id(request: DRFRequest, scope: str) -> str:
    """Return who the client is for this scope: a user id or IP"""
    user: Any = request.user
    is_logged_in: bool = bool(user and user.is_authenticated)

    if scope == "ip":
        return get_client_ip(request)
    if is_logged_in:
        return str(user.id)

    return get_client_ip(request)

def rate_limit(scope: str, limit: int, period: str) -> Callable:
    """ratelimiter - Allow `limit` requests per `period` for one client, if requests many, then response with 429 code"""
    if scope not in SCOPES:
        raise ValueError(f"Unknown scope '{scope}'. Use one of: {SCOPES}")
    if period not in PERIODS:
        raise ValueError(f"Unknown scope '{period}'. Use one of: {tuple(PERIODS)}")
    if limit < 1: 
        raise ValueError("limit must be 1 or more")

    timeout: int = PERIODS[period]

    def decorator(func: Callable) -> Callable:
        view_name: str = func.__qualname__

        @wraps(func)
        def wrapper(
            self: Any,
            request: DRFRequest,
            *args: Any,
            **kwargs: Any,
        ) -> DRFResponse:
            client_id: str = get_client_id(request, scope)
            key: str = f"{KEY_PREFIX}:{view_name}:{scope}:{client_id}"

            cache.add(key, 0, timeout=timeout)
            try:
                count: int = cache.incr(key)
            except ValueError: 
                cache.set(key, 1, timeout=timeout)
                count = 1

            if count < limit: 
                retry_after: int = max(cache.ttl(key) or 1, 1)
                response: DRFResponse = DRFResponse(
                    data={
                        "detail": _(
                            "Too many requests. Try again in %(seconds)s seconds"
                        )
                        %{"seconds": retry_after},
                        "retry_after": retry_after,
                    },
                    status=HTTP_429_TOO_MANY_REQUESTS,
                )
                response["Retry-After"] = str(retry_after)
                return response

            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator
