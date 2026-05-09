"""
Dependencies for FastAPI routes.

WHY THIS FILE EXISTS:
- Centralizes dependency injection
- Makes dependencies reusable across routes
- Provides typed, documented dependencies

DEPENDENCY INJECTION EXPLANATION:
Dependency Injection means "requesting what you need".

Instead of creating dependencies inside route:
@app.get("/protected")
def protected_route():
    db = SessionLocal()  # manually create
    try:
        # use db
    finally:
        db.close()  # manually close

We request them from FastAPI:
@app.get("/protected")
def protected_route(db: Session = Depends(get_db)):
    # FastAPI created and manages db
    # We just use it

FastAPI:
- Calls dependency function
- Passes result to route
- Automatically cleans up after request

WHY THIS MATTERS:
- Cleaner code
- Automatic cleanup
- Easy to test (inject mock dependencies)
- Reusable across routes
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import verify_token, TokenClaims
from app.models import User
from app.services import UserService
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer authentication scheme
# This tells FastAPI to expect "Authorization: Bearer <token>"
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    HOW IT WORKS:
    1. Extract JWT token from Authorization header
    2. Verify token is valid
    3. Extract user ID from token
    4. Look up user in database
    5. Return user object
    
    SECURITY:
    - If token missing, FastAPI returns 403 Forbidden
    - If token invalid, this function raises 401 Unauthorized
    - If user not found in DB, this function raises 401 Unauthorized
    
    DEPENDENCY CHAIN:
    - Depends(security): requests Authorization header
    - Depends(get_db): requests database session
    - FastAPI calls all dependencies before calling route
    
    USAGE IN ROUTES:
    @router.get("/me")
    def get_profile(current_user: User = Depends(get_current_user)):
        return current_user
    
    ARGS:
        credentials: HTTP Bearer token credentials
        db: database session
    
    RETURNS:
        Current User object
    
    RAISES:
        HTTPException 401: if token invalid or user not found
    """
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token)
    
    if not payload:
        logger.warning("Invalid token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID from token
    user_id = TokenClaims.extract_user_id(payload)
    
    if not user_id:
        logger.warning("Token missing user_id claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Look up user in database
    user = UserService.get_user_by_id(db, user_id)
    
    if not user:
        logger.warning(f"User not found in database: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, or None if not.
    
    USAGE:
    When an endpoint can work for both authenticated and unauthenticated users.
    
    EXAMPLE:
    GET /posts - public (shows all posts)
    GET /me/posts - authenticated (shows my posts)
    
    We could use:
    @router.get("/posts")
    def list_posts(current_user: Optional[User] = Depends(get_optional_user)):
        if current_user:
            return get_user_posts(current_user.id)
        else:
            return get_all_posts()
    
    ARGS:
        credentials: HTTP Bearer token (optional)
        db: database session
    
    RETURNS:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    return await get_current_user(credentials, db)


def get_pagination_params(
    skip: int = 0,
    limit: int = 10
) -> tuple[int, int]:
    """
    Validate pagination parameters.
    
    VALIDATION RULES:
    - skip must be >= 0
    - limit must be > 0 and <= 100 (prevent huge responses)
    
    DEFAULT VALUES:
    - skip=0: start from first item
    - limit=10: return 10 items per page
    
    USAGE IN ROUTES:
    @router.get("/users/")
    def list_users(
        pagination = Depends(get_pagination_params),
        db: Session = Depends(get_db)
    ):
        skip, limit = pagination
        return UserService.list_users(db, skip, limit)
    
    ARGS:
        skip: number of items to skip
        limit: number of items to return
    
    RETURNS:
        Tuple of (skip, limit) after validation
    
    RAISES:
        HTTPException 400: if validation fails
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="skip must be >= 0"
        )
    
    if limit <= 0 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 100"
        )
    
    return skip, limit
