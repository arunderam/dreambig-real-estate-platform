"""
Rate limiting implementation for API endpoints
"""
import time
import redis
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_limit = 60  # requests per minute
        self.default_window = 60  # seconds
    
    def is_allowed(
        self, 
        key: str, 
        limit: int = None, 
        window: int = None
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit
        Returns (is_allowed, rate_limit_info)
        """
        limit = limit or self.default_limit
        window = window or self.default_window
        
        current_time = int(time.time())
        window_start = current_time - window
        
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiry
        pipe.expire(key, window)
        
        results = pipe.execute()
        current_requests = results[1]
        
        rate_limit_info = {
            "limit": limit,
            "remaining": max(0, limit - current_requests - 1),
            "reset": current_time + window,
            "retry_after": window if current_requests >= limit else 0
        }
        
        is_allowed = current_requests < limit
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for key: {key}")
        
        return is_allowed, rate_limit_info
    
    def get_client_key(self, request: Request, identifier: str = None) -> str:
        """Generate rate limit key for client"""
        if identifier:
            return f"rate_limit:{identifier}"
        
        # Use IP address as fallback
        client_ip = self._get_client_ip(request)
        return f"rate_limit:ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        try:
            redis_client = redis.from_url("redis://localhost:6379/0")
            _rate_limiter = RateLimiter(redis_client)
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
            # Fallback to in-memory rate limiter
            _rate_limiter = InMemoryRateLimiter()
    
    return _rate_limiter

class InMemoryRateLimiter:
    """In-memory rate limiter fallback"""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.default_limit = 60
        self.default_window = 60
    
    def is_allowed(
        self, 
        key: str, 
        limit: int = None, 
        window: int = None
    ) -> tuple[bool, Dict[str, Any]]:
        """In-memory rate limiting"""
        limit = limit or self.default_limit
        window = window or self.default_window
        
        current_time = time.time()
        window_start = current_time - window
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key] 
                if req_time > window_start
            ]
        else:
            self.requests[key] = []
        
        current_requests = len(self.requests[key])
        
        rate_limit_info = {
            "limit": limit,
            "remaining": max(0, limit - current_requests - 1),
            "reset": int(current_time + window),
            "retry_after": window if current_requests >= limit else 0
        }
        
        is_allowed = current_requests < limit
        
        if is_allowed:
            self.requests[key].append(current_time)
        
        return is_allowed, rate_limit_info
    
    def get_client_key(self, request: Request, identifier: str = None) -> str:
        """Generate rate limit key for client"""
        if identifier:
            return f"rate_limit:{identifier}"
        
        client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:ip:{client_ip}"

def rate_limit(
    limit: int = 60,
    window: int = 60,
    key_func: callable = None,
    skip_successful_requests: bool = False
):
    """
    Rate limiting decorator for FastAPI endpoints
    
    Args:
        limit: Number of requests allowed per window
        window: Time window in seconds
        key_func: Function to generate rate limit key
        skip_successful_requests: Only count failed requests
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object in arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no request found, skip rate limiting
                return await func(*args, **kwargs)
            
            rate_limiter = get_rate_limiter()
            
            # Generate rate limit key
            if key_func:
                key = key_func(request)
            else:
                key = rate_limiter.get_client_key(request)
            
            # Check rate limit
            is_allowed, rate_info = rate_limiter.is_allowed(key, limit, window)
            
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_info["remaining"]),
                        "X-RateLimit-Reset": str(rate_info["reset"]),
                        "Retry-After": str(rate_info["retry_after"])
                    }
                )
            
            # Execute the function
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                # If skip_successful_requests is True, remove the request from count
                # on successful execution (this is a failed request)
                if not skip_successful_requests:
                    raise
                
                # For failed requests, we keep the count
                raise
        
        return wrapper
    return decorator

def user_rate_limit(limit: int = 100, window: int = 60):
    """Rate limit by authenticated user"""
    def key_func(request: Request) -> str:
        # Try to get user from request state (set by auth middleware)
        user = getattr(request.state, 'user', None)
        if user:
            return f"rate_limit:user:{user.id}"
        
        # Fallback to IP-based rate limiting
        rate_limiter = get_rate_limiter()
        return rate_limiter.get_client_key(request)
    
    return rate_limit(limit=limit, window=window, key_func=key_func)

def endpoint_rate_limit(endpoint: str, limit: int = 30, window: int = 60):
    """Rate limit by endpoint"""
    def key_func(request: Request) -> str:
        client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:endpoint:{endpoint}:ip:{client_ip}"
    
    return rate_limit(limit=limit, window=window, key_func=key_func)

def auth_rate_limit(limit: int = 10, window: int = 60):
    """Strict rate limiting for authentication endpoints"""
    def key_func(request: Request) -> str:
        client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:auth:ip:{client_ip}"
    
    return rate_limit(limit=limit, window=window, key_func=key_func)

class RateLimitMiddleware:
    """Middleware to add rate limit headers to all responses"""
    
    def __init__(self, app, rate_limiter: RateLimiter = None):
        self.app = app
        self.rate_limiter = rate_limiter or get_rate_limiter()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Check rate limit for general requests
        key = self.rate_limiter.get_client_key(request)
        is_allowed, rate_info = self.rate_limiter.is_allowed(key)
        
        if not is_allowed:
            response = HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
            await send({
                "type": "http.response.start",
                "status": response.status_code,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"x-ratelimit-limit", str(rate_info["limit"]).encode()],
                    [b"x-ratelimit-remaining", str(rate_info["remaining"]).encode()],
                    [b"x-ratelimit-reset", str(rate_info["reset"]).encode()],
                    [b"retry-after", str(rate_info["retry_after"]).encode()],
                ]
            })
            await send({
                "type": "http.response.body",
                "body": json.dumps({"detail": "Rate limit exceeded"}).encode()
            })
            return
        
        # Add rate limit info to request state
        request.state.rate_limit_info = rate_info
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([
                    [b"x-ratelimit-limit", str(rate_info["limit"]).encode()],
                    [b"x-ratelimit-remaining", str(rate_info["remaining"]).encode()],
                    [b"x-ratelimit-reset", str(rate_info["reset"]).encode()],
                ])
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
