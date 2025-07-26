"""
CSRF (Cross-Site Request Forgery) protection implementation
"""
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
import logging

logger = logging.getLogger(__name__)

class CSRFProtection:
    """CSRF protection manager"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        self.token_expiry_hours = 24
        self.header_name = "X-CSRF-Token"
        self.cookie_name = "csrf_token"
        self.form_field_name = "csrf_token"
    
    def generate_csrf_token(self, session_id: str = None) -> str:
        """Generate a CSRF token"""
        if not session_id:
            session_id = secrets.token_urlsafe(16)
        
        # Create timestamp
        timestamp = str(int(datetime.utcnow().timestamp()))
        
        # Create token data
        token_data = f"{session_id}:{timestamp}"
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key,
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{token_data}:{signature}"
    
    def validate_csrf_token(self, token: str, session_id: str = None) -> bool:
        """Validate CSRF token"""
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False
            
            token_session_id, timestamp, signature = parts
            
            # If session_id is provided, verify it matches
            if session_id and token_session_id != session_id:
                logger.warning(f"CSRF token session ID mismatch")
                return False
            
            # Verify signature
            token_data = f"{token_session_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key,
                token_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("CSRF token signature verification failed")
                return False
            
            # Check expiry
            token_time = datetime.fromtimestamp(int(timestamp))
            expiry_time = token_time + timedelta(hours=self.token_expiry_hours)
            
            if datetime.utcnow() > expiry_time:
                logger.info("CSRF token expired")
                return False
            
            return True
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid CSRF token format: {e}")
            return False
    
    def get_csrf_token_from_request(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request"""
        # Try header first
        token = request.headers.get(self.header_name)
        if token:
            return token
        
        # Try form data
        if hasattr(request, 'form'):
            form_data = getattr(request, 'form', {})
            token = form_data.get(self.form_field_name)
            if token:
                return token
        
        # Try query parameters
        token = request.query_params.get(self.form_field_name)
        if token:
            return token
        
        return None
    
    def get_session_id_from_request(self, request: Request) -> Optional[str]:
        """Extract session ID from request"""
        # Try to get from session cookie or custom header
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = request.headers.get("X-Session-ID")
        
        return session_id
    
    def set_csrf_cookie(self, response: Response, token: str):
        """Set CSRF token as HTTP-only cookie"""
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.token_expiry_hours * 3600,
            httponly=True,
            secure=True,  # Use HTTPS in production
            samesite="strict"
        )

# Global CSRF protection instance
_csrf_protection: Optional[CSRFProtection] = None

def get_csrf_protection() -> CSRFProtection:
    """Get global CSRF protection instance"""
    global _csrf_protection
    if _csrf_protection is None:
        # Use a default secret key (should be configured properly)
        secret_key = "your-csrf-secret-key-change-this"
        _csrf_protection = CSRFProtection(secret_key)
    
    return _csrf_protection

def csrf_protect(exempt_methods: list = None):
    """
    Decorator for CSRF protection
    
    Args:
        exempt_methods: HTTP methods to exempt from CSRF protection (default: GET, HEAD, OPTIONS)
    """
    if exempt_methods is None:
        exempt_methods = ["GET", "HEAD", "OPTIONS"]
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find request object in arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no request found, skip CSRF protection
                return await func(*args, **kwargs)
            
            # Skip CSRF protection for exempt methods
            if request.method in exempt_methods:
                return await func(*args, **kwargs)
            
            csrf_protection = get_csrf_protection()
            
            # Get CSRF token from request
            csrf_token = csrf_protection.get_csrf_token_from_request(request)
            if not csrf_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing"
                )
            
            # Get session ID
            session_id = csrf_protection.get_session_id_from_request(request)
            
            # Validate CSRF token
            if not csrf_protection.validate_csrf_token(csrf_token, session_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token invalid"
                )
            
            # Execute the function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

class CSRFMiddleware:
    """Middleware to handle CSRF protection"""
    
    def __init__(self, app, csrf_protection: CSRFProtection = None):
        self.app = app
        self.csrf_protection = csrf_protection or get_csrf_protection()
        self.exempt_paths = ["/api/docs", "/api/redoc", "/api/openapi.json"]
        self.exempt_methods = ["GET", "HEAD", "OPTIONS"]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip CSRF protection for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            await self.app(scope, receive, send)
            return
        
        # Skip CSRF protection for exempt methods
        if request.method in self.exempt_methods:
            await self.app(scope, receive, send)
            return
        
        # Check CSRF token for state-changing requests
        csrf_token = self.csrf_protection.get_csrf_token_from_request(request)
        session_id = self.csrf_protection.get_session_id_from_request(request)
        
        if not csrf_token or not self.csrf_protection.validate_csrf_token(csrf_token, session_id):
            response = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing or invalid"
            )
            await send({
                "type": "http.response.start",
                "status": response.status_code,
                "headers": [[b"content-type", b"application/json"]]
            })
            await send({
                "type": "http.response.body",
                "body": b'{"detail": "CSRF token missing or invalid"}'
            })
            return
        
        await self.app(scope, receive, send)

def generate_csrf_token(session_id: str = None) -> str:
    """Generate a CSRF token"""
    csrf_protection = get_csrf_protection()
    return csrf_protection.generate_csrf_token(session_id)

def validate_csrf_token(token: str, session_id: str = None) -> bool:
    """Validate a CSRF token"""
    csrf_protection = get_csrf_protection()
    return csrf_protection.validate_csrf_token(token, session_id)

def set_csrf_cookie(response: Response, token: str):
    """Set CSRF token as cookie"""
    csrf_protection = get_csrf_protection()
    csrf_protection.set_csrf_cookie(response, token)

# FastAPI dependency for CSRF protection
class CSRFBearer(HTTPBearer):
    """FastAPI dependency for CSRF token validation"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.csrf_protection = get_csrf_protection()
    
    async def __call__(self, request: Request) -> Optional[str]:
        # Get CSRF token
        csrf_token = self.csrf_protection.get_csrf_token_from_request(request)
        
        if not csrf_token:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing"
                )
            return None
        
        # Get session ID
        session_id = self.csrf_protection.get_session_id_from_request(request)
        
        # Validate token
        if not self.csrf_protection.validate_csrf_token(csrf_token, session_id):
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token invalid"
                )
            return None
        
        return csrf_token

# Create CSRF dependency instance
csrf_bearer = CSRFBearer()
