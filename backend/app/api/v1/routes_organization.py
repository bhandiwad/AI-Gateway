from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.core.security import get_current_user
from backend.app.core.permissions import require_permission, Permission
from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.schemas.organization import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentWithStats,
    TeamCreate, TeamUpdate, TeamResponse, TeamWithStats,
    TeamMemberAdd, TeamMemberRemove,
    OrganizationStats
)
from backend.app.services.organization_service import organization_service

router = APIRouter()


# ==================== DEPARTMENT ENDPOINTS ====================

@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    department: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.SETTINGS_EDIT)
):
    """Create a new department."""
    return organization_service.create_department(
        db=db,
        tenant_id=current_user["sub"],
        department_data=department
    )


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.DASHBOARD_VIEW)
):
    """List all departments."""
    return organization_service.list_departments(
        db=db,
        tenant_id=current_user["sub"],
        skip=skip,
        limit=limit,
        is_active=is_active
    )


@router.get("/departments/{department_id}", response_model=DepartmentWithStats)
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.DASHBOARD_VIEW)
):
    """Get department by ID with statistics."""
    department = organization_service.get_department_stats(
        db=db,
        department_id=department_id,
        tenant_id=current_user["sub"]
    )
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    return department


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.SETTINGS_EDIT)
):
    """Update department."""
    department = organization_service.update_department(
        db=db,
        department_id=department_id,
        tenant_id=current_user["sub"],
        update_data=department_update
    )
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    return department


@router.delete("/departments/{department_id}")
async def delete_department(
    department_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.SETTINGS_EDIT)
):
    """Delete department (soft delete)."""
    success = organization_service.delete_department(
        db=db,
        department_id=department_id,
        tenant_id=current_user["sub"]
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    return {"message": "Department deleted successfully"}


# ==================== TEAM ENDPOINTS ====================

@router.post("/teams", response_model=TeamResponse)
async def create_team(
    team: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.USERS_CREATE)
):
    """Create a new team."""
    return organization_service.create_team(
        db=db,
        tenant_id=current_user["sub"],
        team_data=team
    )


@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    department_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.DASHBOARD_VIEW)
):
    """List all teams."""
    return organization_service.list_teams(
        db=db,
        tenant_id=current_user["sub"],
        department_id=department_id,
        skip=skip,
        limit=limit,
        is_active=is_active
    )


@router.get("/teams/{team_id}", response_model=TeamWithStats)
async def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.DASHBOARD_VIEW)
):
    """Get team by ID with statistics."""
    team = organization_service.get_team_stats(
        db=db,
        team_id=team_id,
        tenant_id=current_user["sub"]
    )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.USERS_EDIT)
):
    """Update team."""
    team = organization_service.update_team(
        db=db,
        team_id=team_id,
        tenant_id=current_user["sub"],
        update_data=team_update
    )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.USERS_EDIT)
):
    """Delete team (soft delete)."""
    success = organization_service.delete_team(
        db=db,
        team_id=team_id,
        tenant_id=current_user["sub"]
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return {"message": "Team deleted successfully"}


# ==================== TEAM MEMBER ENDPOINTS ====================

@router.post("/teams/{team_id}/members")
async def add_team_member(
    team_id: int,
    member: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.USERS_EDIT)
):
    """Add member to team."""
    success = organization_service.add_team_member(
        db=db,
        team_id=team_id,
        user_id=member.user_id,
        tenant_id=current_user["sub"],
        role=member.role
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not add member to team"
        )
    return {"message": "Member added successfully"}


@router.delete("/teams/{team_id}/members")
async def remove_team_member(
    team_id: int,
    member: TeamMemberRemove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.USERS_EDIT)
):
    """Remove member from team."""
    success = organization_service.remove_team_member(
        db=db,
        team_id=team_id,
        user_id=member.user_id,
        tenant_id=current_user["sub"]
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in team"
        )
    return {"message": "Member removed successfully"}


@router.get("/teams/{team_id}/members")
async def list_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.DASHBOARD_VIEW)
):
    """List all members of a team."""
    members = organization_service.list_team_members(
        db=db,
        team_id=team_id,
        tenant_id=current_user["sub"]
    )
    return members


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/stats", response_model=OrganizationStats)
async def get_organization_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.DASHBOARD_VIEW)
):
    """Get organization-wide statistics."""
    return organization_service.get_organization_stats(
        db=db,
        tenant_id=current_user["sub"]
    )
