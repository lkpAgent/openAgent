"""
中间件管理，如上下文中间件：校验Token等
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable

from ..db.database import get_db_session
from ..services.auth import AuthService
from .context import UserContext


class UserContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set user context for authenticated requests."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        # Paths that don't require authentication
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register", 
            "/api/auth/login-oauth",
            "/auth/login",
            "/auth/register",
            "/auth/login-oauth",
            "/health",
            "/test"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and set user context if authenticated."""
        import logging
        logging.info(f"[MIDDLEWARE] Processing request: {request.method} {request.url.path}")
        
        # Skip authentication for excluded paths
        path = request.url.path
        logging.info(f"[MIDDLEWARE] Checking path: {path} against exclude_paths: {self.exclude_paths}")
        
        should_skip = False
        for exclude_path in self.exclude_paths:
            # Exact match
            if path == exclude_path:
                should_skip = True
                logging.info(f"[MIDDLEWARE] Path {path} exactly matches exclude_path {exclude_path}")
                break
            # For paths ending with '/', check if request path starts with it
            elif exclude_path.endswith('/') and path.startswith(exclude_path):
                should_skip = True
                logging.info(f"[MIDDLEWARE] Path {path} starts with exclude_path {exclude_path}")
                break
            # For paths not ending with '/', check if request path starts with it + '/'
            elif not exclude_path.endswith('/') and exclude_path != '/' and path.startswith(exclude_path + '/'):
                should_skip = True
                logging.info(f"[MIDDLEWARE] Path {path} starts with exclude_path {exclude_path}/")
                break
        
        if should_skip:
            logging.info(f"[MIDDLEWARE] Skipping authentication for excluded path: {path}")
            response = await call_next(request)
            return response
        
        logging.info(f"[MIDDLEWARE] Processing authenticated request: {path}")
        
        # Always clear any existing user context to ensure fresh authentication
        UserContext.clear_current_user()
        
        # Initialize context token
        user_token = None
        
        # Try to extract and validate token
        try:
            # Get authorization header
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                # No token provided, return 401 error
                from fastapi import HTTPException, status
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Missing or invalid authorization header"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Extract token
            token = authorization.split(" ")[1]
            
            # Verify token
            payload = AuthService.verify_token(token)
            if payload is None:
                # Invalid token, return 401 error
                from fastapi import HTTPException, status
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Get username from token
            username = payload.get("sub")
            if not username:
                from fastapi import HTTPException, status
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token payload"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Get user from database
            db = get_db_session()
            try:
                from ..models.user import User
                user = db.query(User).filter(User.username == username).first()
                if not user:
                    from fastapi import HTTPException, status
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "User not found"},
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                
                if not user.is_active:
                    from fastapi import HTTPException, status
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "User account is inactive"},
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                
                # Set user in context using token mechanism
                user_token = UserContext.set_current_user_with_token(user)
                import logging
                logging.info(f"User {user.username} (ID: {user.id}) authenticated and set in context")
                
                # Verify context is set correctly
                current_user_id = UserContext.get_current_user_id()
                logging.info(f"Verified current user ID in context: {current_user_id}")
            finally:
                db.close()
            
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logging.warning(f"Error setting user context: {e}")
        
        # Continue with request
        try:
            response = await call_next(request)
            return response
        finally:
            # Always clear user context after request processing
            UserContext.clear_current_user()
            logging.debug(f"[MIDDLEWARE] Cleared user context after processing request: {path}")