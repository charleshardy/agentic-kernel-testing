"""Authentication endpoints."""

from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from ..models import APIResponse
from ..auth import (
    authenticate_user, create_access_token, get_current_user, 
    revoke_token, revoke_user_tokens, generate_api_key,
    cleanup_expired_tokens, get_active_tokens_count
)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]


class APIKeyRequest(BaseModel):
    """API key generation request."""
    description: str = ""


@router.post("/auth/login", response_model=APIResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return access token."""
    user = authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(user)
    
    login_response = LoginResponse(
        access_token=access_token,
        expires_in=3600,  # 1 hour in seconds
        user_info={
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "permissions": user["permissions"]
        }
    )
    
    return APIResponse(
        success=True,
        message="Login successful",
        data=login_response.dict()
    )


@router.post("/auth/logout", response_model=APIResponse)
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout user and revoke current token."""
    token = current_user.get("token")
    
    if token and revoke_token(token):
        return APIResponse(
            success=True,
            message="Logout successful",
            data={"revoked_token": True}
        )
    
    return APIResponse(
        success=True,
        message="Logout completed",
        data={"revoked_token": False}
    )


@router.post("/auth/revoke-all", response_model=APIResponse)
async def revoke_all_tokens(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Revoke all tokens for the current user."""
    user_id = current_user["user_id"]
    revoked_count = revoke_user_tokens(user_id)
    
    return APIResponse(
        success=True,
        message=f"Revoked {revoked_count} tokens",
        data={
            "revoked_tokens": revoked_count,
            "user_id": user_id
        }
    )


@router.post("/auth/api-key", response_model=APIResponse)
async def create_api_key(
    api_key_request: APIKeyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate a long-lived API key for programmatic access."""
    api_key = generate_api_key(
        current_user["user_id"], 
        api_key_request.description
    )
    
    return APIResponse(
        success=True,
        message="API key generated successfully",
        data={
            "api_key": api_key,
            "description": api_key_request.description,
            "expires_in_days": 365,
            "created_for": current_user["username"]
        }
    )


@router.get("/auth/me", response_model=APIResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information."""
    return APIResponse(
        success=True,
        message="User information retrieved",
        data={
            "user": current_user,
            "session_info": {
                "authenticated": True,
                "login_time": current_user.get("last_login", datetime.utcnow()).isoformat() if current_user.get("last_login") else None
            }
        }
    )


@router.get("/auth/tokens", response_model=APIResponse)
async def get_token_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get information about active tokens (admin only)."""
    if "system:admin" not in current_user.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )
    
    # Clean up expired tokens first
    expired_count = cleanup_expired_tokens()
    active_count = get_active_tokens_count()
    
    return APIResponse(
        success=True,
        message="Token information retrieved",
        data={
            "active_tokens": active_count,
            "expired_tokens_cleaned": expired_count,
            "cleanup_timestamp": datetime.utcnow().isoformat()
        }
    )