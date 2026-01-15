"""User and Team Management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from ..auth import get_current_user
from ..models import APIResponse

router = APIRouter(prefix="/users")


# Request/Response Models
class User(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str
    role: str
    teams: List[str]
    status: str
    created_at: datetime
    last_login: Optional[datetime]


class Team(BaseModel):
    id: str
    name: str
    description: str
    members: List[str]
    owner: str
    created_at: datetime
    workspace_id: Optional[str]


class Role(BaseModel):
    id: str
    name: str
    description: str
    permissions: List[str]
    is_system_role: bool


class Permission(BaseModel):
    id: str
    name: str
    resource: str
    action: str
    description: str


@router.get("/", response_model=APIResponse)
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    team: Optional[str] = Query(None, description="Filter by team"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List all users."""
    users = [
        User(
            id="user-001",
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            role="admin",
            teams=["team-001", "team-002"],
            status="active",
            created_at=datetime.now(),
            last_login=datetime.now()
        ),
        User(
            id="user-002",
            username="developer",
            email="dev@example.com",
            full_name="Developer User",
            role="developer",
            teams=["team-001"],
            status="active",
            created_at=datetime.now(),
            last_login=datetime.now()
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(users)} users",
        data={"users": [u.dict() for u in users], "total": len(users)}
    )


@router.get("/{user_id}", response_model=APIResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user details."""
    user = User(
        id=user_id,
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        role="admin",
        teams=["team-001", "team-002"],
        status="active",
        created_at=datetime.now(),
        last_login=datetime.now()
    )
    
    return APIResponse(
        success=True,
        message="User retrieved successfully",
        data=user.dict()
    )


@router.get("/teams/list", response_model=APIResponse)
async def list_teams(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List all teams."""
    teams = [
        Team(
            id="team-001",
            name="Kernel Development",
            description="Linux kernel development team",
            members=["user-001", "user-002", "user-003"],
            owner="user-001",
            created_at=datetime.now(),
            workspace_id="ws-001"
        ),
        Team(
            id="team-002",
            name="QA Team",
            description="Quality assurance and testing",
            members=["user-001", "user-004"],
            owner="user-001",
            created_at=datetime.now(),
            workspace_id="ws-002"
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(teams)} teams",
        data={"teams": [t.dict() for t in teams], "total": len(teams)}
    )


@router.get("/roles/list", response_model=APIResponse)
async def list_roles(current_user: dict = Depends(get_current_user)):
    """List all roles."""
    roles = [
        Role(
            id="role-001",
            name="admin",
            description="Full system access",
            permissions=["*"],
            is_system_role=True
        ),
        Role(
            id="role-002",
            name="developer",
            description="Development and testing access",
            permissions=["test.create", "test.execute", "test.view"],
            is_system_role=True
        ),
        Role(
            id="role-003",
            name="viewer",
            description="Read-only access",
            permissions=["test.view", "results.view"],
            is_system_role=True
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(roles)} roles",
        data={"roles": [r.dict() for r in roles]}
    )


@router.get("/permissions/list", response_model=APIResponse)
async def list_permissions(current_user: dict = Depends(get_current_user)):
    """List all available permissions."""
    permissions = [
        Permission(
            id="perm-001",
            name="test.create",
            resource="test",
            action="create",
            description="Create new tests"
        ),
        Permission(
            id="perm-002",
            name="test.execute",
            resource="test",
            action="execute",
            description="Execute tests"
        ),
        Permission(
            id="perm-003",
            name="test.view",
            resource="test",
            action="view",
            description="View test details"
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(permissions)} permissions",
        data={"permissions": [p.dict() for p in permissions]}
    )


@router.post("/", response_model=APIResponse)
async def create_user(
    user: User,
    current_user: dict = Depends(get_current_user)
):
    """Create a new user."""
    return APIResponse(
        success=True,
        message=f"User {user.username} created successfully",
        data={"user_id": "user-new"}
    )


@router.put("/{user_id}", response_model=APIResponse)
async def update_user(
    user_id: str,
    user: User,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing user."""
    return APIResponse(
        success=True,
        message=f"User {user_id} updated successfully",
        data={"user_id": user_id}
    )


@router.post("/teams", response_model=APIResponse)
async def create_team(
    team: Team,
    current_user: dict = Depends(get_current_user)
):
    """Create a new team."""
    return APIResponse(
        success=True,
        message=f"Team {team.name} created successfully",
        data={"team_id": "team-new"}
    )


@router.put("/teams/{team_id}/members", response_model=APIResponse)
async def update_team_members(
    team_id: str,
    member_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Update team members."""
    return APIResponse(
        success=True,
        message=f"Team {team_id} members updated",
        data={"team_id": team_id, "member_count": len(member_ids)}
    )
