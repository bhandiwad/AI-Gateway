from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.db.session import get_db
from backend.app.core.security import get_current_tenant, get_current_user
from backend.app.core.permissions import Permission, RequirePermission
from backend.app.db.models.tenant import Tenant
from backend.app.db.models.user import UserRole, UserStatus
from backend.app.services.user_service import user_service
from backend.app.services.audit_service import audit_service
from backend.app.db.models.audit_log import AuditAction
from backend.app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserUsageSummary
)

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    current_user: dict = Depends(RequirePermission(Permission.USERS_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    status_filter = UserStatus(status) if status else None
    users = user_service.get_users_by_tenant(
        db, tenant.id, skip=skip, limit=limit, status=status_filter
    )
    return users


@router.get("/users/count")
async def count_users(
    status: Optional[str] = None,
    current_user: dict = Depends(RequirePermission(Permission.USERS_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    status_filter = UserStatus(status) if status else None
    total = user_service.count_users_by_tenant(db, tenant.id, status=status_filter)
    active = user_service.count_users_by_tenant(db, tenant.id, status=UserStatus.ACTIVE)
    return {"total": total, "active": active}


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(RequirePermission(Permission.USERS_CREATE)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    existing = user_service.get_user_by_email(db, tenant.id, user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user = user_service.create_user(
        db=db,
        tenant_id=tenant.id,
        email=user_data.email,
        name=user_data.name,
        password=user_data.password,
        role=UserRole(user_data.role.value),
        allowed_models=user_data.allowed_models,
        rate_limit=user_data.rate_limit,
        monthly_budget=user_data.monthly_budget
    )
    
    audit_service.log(
        db=db,
        tenant_id=tenant.id,
        action=AuditAction.USER_CREATED,
        resource_type="user",
        resource_id=str(user.id),
        description=f"Created user {user.email}",
        new_value={"email": user.email, "name": user.name, "role": user.role.value}
    )
    
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(RequirePermission(Permission.USERS_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    user = user_service.get_user_by_id(db, user_id)
    if not user or user.tenant_id != tenant.id:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    updates: UserUpdate,
    current_user: dict = Depends(RequirePermission(Permission.USERS_EDIT)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    user = user_service.get_user_by_id(db, user_id)
    if not user or user.tenant_id != tenant.id:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_values = {
        "name": user.name,
        "role": user.role.value if user.role else None,
        "status": user.status.value if user.status else None
    }
    
    update_dict = updates.model_dump(exclude_unset=True)
    if "role" in update_dict and update_dict["role"]:
        update_dict["role"] = UserRole(update_dict["role"].value)
    if "status" in update_dict and update_dict["status"]:
        update_dict["status"] = UserStatus(update_dict["status"].value)
    
    updated_user = user_service.update_user(db, user_id, update_dict)
    
    audit_service.log(
        db=db,
        tenant_id=tenant.id,
        action=AuditAction.USER_UPDATED,
        resource_type="user",
        resource_id=str(user_id),
        description=f"Updated user {user.email}",
        old_value=old_values,
        new_value=update_dict
    )
    
    return updated_user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(RequirePermission(Permission.USERS_DELETE)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    user = user_service.get_user_by_id(db, user_id)
    if not user or user.tenant_id != tenant.id:
        raise HTTPException(status_code=404, detail="User not found")
    
    email = user.email
    success = user_service.delete_user(db, user_id)
    
    if success:
        audit_service.log(
            db=db,
            tenant_id=tenant.id,
            action=AuditAction.USER_DELETED,
            resource_type="user",
            resource_id=str(user_id),
            description=f"Deleted user {email}"
        )
    
    return {"success": success, "message": f"User {email} deleted"}


@router.get("/users/{user_id}/usage", response_model=UserUsageSummary)
async def get_user_usage(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(RequirePermission(Permission.USERS_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    user = user_service.get_user_by_id(db, user_id)
    if not user or user.tenant_id != tenant.id:
        raise HTTPException(status_code=404, detail="User not found")
    
    summary = user_service.get_user_usage_summary(db, user_id, days)
    return {"user_id": user_id, **summary}


@router.post("/users/reset-spend")
async def reset_monthly_spend(
    current_user: dict = Depends(RequirePermission(Permission.BILLING_INVOICE)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    count = user_service.reset_monthly_spend(db, tenant.id)
    
    audit_service.log(
        db=db,
        tenant_id=tenant.id,
        action=AuditAction.ADMIN_ACTION,
        description=f"Reset monthly spend for {count} users"
    )
    
    return {"success": True, "users_reset": count}
