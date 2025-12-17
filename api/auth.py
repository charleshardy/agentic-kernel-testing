"""Authentication and authorization for the API."""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from config.settings import Settings

settings = Settings()
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data."""
    username: str
    user_id: str
    permissions: List[str]
    expires_at: datetime


class User(BaseModel):
    """User model for authentication."""
    user_id: str
    username: str
    email: str
    permissions: List[str]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None


# In-memory user store (in production, this would be a database)
USERS_DB = {
    "admin": {
        "user_id": "admin-001",
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "permissions": [
            "test:submit",
            "test:read",
            "test:delete",
            "status:read",
            "results:read",
            "system:admin"
        ],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    },
    "developer": {
        "user_id": "dev-001", 
        "username": "developer",
        "email": "dev@example.com",
        "password_hash": hashlib.sha256("dev123".encode()).hexdigest(),
        "permissions": [
            "test:submit",
            "test:read",
            "status:read",
            "results:read"
        ],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    },
    "readonly": {
        "user_id": "ro-001",
        "username": "readonly",
        "email": "readonly@example.com", 
        "password_hash": hashlib.sha256("readonly123".encode()).hexdigest(),
        "permissions": [
            "test:read",
            "status:read",
            "results:read"
        ],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    },
    "demo": {
        "user_id": "demo-001",
        "username": "demo",
        "email": "demo@example.com",
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "permissions": [
            "test:submit",
            "test:read",
            "test:delete"
        ],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
}

# In-memory token store (in production, use Redis or database)
ACTIVE_TOKENS = {}


def create_access_token(user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.api.token_expire_hours)
    
    to_encode = {
        "sub": user_data["username"],
        "user_id": user_data["user_id"],
        "permissions": user_data["permissions"],
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.api.secret_key, 
        algorithm=settings.api.algorithm
    )
    
    # Store token in active tokens (for revocation)
    ACTIVE_TOKENS[encoded_jwt] = {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "expires_at": expire,
        "created_at": datetime.utcnow()
    }
    
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user data."""
    token = credentials.credentials
    
    # Check if token is in active tokens
    if token not in ACTIVE_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked or is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            token, 
            settings.api.secret_key, 
            algorithms=[settings.api.algorithm]
        )
        
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        permissions: List[str] = payload.get("permissions", [])
        
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user still exists and is active (allow demo users)
        if username != "demo" and (username not in USERS_DB or not USERS_DB[username]["is_active"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "username": username,
            "user_id": user_id,
            "permissions": permissions,
            "token": token
        }
        
    except jwt.ExpiredSignatureError:
        # Remove expired token
        if token in ACTIVE_TOKENS:
            del ACTIVE_TOKENS[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token_data: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """Get current authenticated user."""
    username = token_data["username"]
    
    # Handle demo user specially
    if username == "demo":
        return {
            "username": "demo",
            "user_id": "demo-001",
            "email": "demo@example.com",
            "permissions": ["test:submit", "test:read", "test:delete"],
            "is_active": True
        }
    
    user_data = USERS_DB.get(username)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Update last login
    USERS_DB[username]["last_login"] = datetime.utcnow()
    
    return {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "email": user_data["email"],
        "permissions": user_data["permissions"],
        "is_active": user_data["is_active"],
        "created_at": user_data["created_at"],
        "last_login": user_data["last_login"]
    }


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if permission not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with username and password."""
    user = USERS_DB.get(username)
    if not user:
        return None
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user["password_hash"]:
        return None
    
    if not user["is_active"]:
        return None
    
    return user


def revoke_token(token: str) -> bool:
    """Revoke a specific token."""
    if token in ACTIVE_TOKENS:
        del ACTIVE_TOKENS[token]
        return True
    return False


def revoke_user_tokens(user_id: str) -> int:
    """Revoke all tokens for a specific user."""
    tokens_to_remove = []
    for token, token_data in ACTIVE_TOKENS.items():
        if token_data["user_id"] == user_id:
            tokens_to_remove.append(token)
    
    for token in tokens_to_remove:
        del ACTIVE_TOKENS[token]
    
    return len(tokens_to_remove)


def cleanup_expired_tokens():
    """Clean up expired tokens from memory."""
    now = datetime.utcnow()
    expired_tokens = []
    
    for token, token_data in ACTIVE_TOKENS.items():
        if token_data["expires_at"] < now:
            expired_tokens.append(token)
    
    for token in expired_tokens:
        del ACTIVE_TOKENS[token]
    
    return len(expired_tokens)


def get_active_tokens_count() -> int:
    """Get count of active tokens."""
    cleanup_expired_tokens()
    return len(ACTIVE_TOKENS)


def generate_api_key(user_id: str, description: str = "") -> str:
    """Generate a long-lived API key for programmatic access."""
    # API keys are longer-lived tokens with special prefix
    api_key = f"ak_{secrets.token_urlsafe(32)}"
    
    # Store API key (in production, hash this)
    ACTIVE_TOKENS[api_key] = {
        "user_id": user_id,
        "username": next(
            (user["username"] for user in USERS_DB.values() 
             if user["user_id"] == user_id), 
            "unknown"
        ),
        "expires_at": datetime.utcnow() + timedelta(days=365),  # 1 year
        "created_at": datetime.utcnow(),
        "type": "api_key",
        "description": description
    }
    
    return api_key