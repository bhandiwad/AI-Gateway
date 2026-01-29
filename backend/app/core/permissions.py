from enum import Enum
from typing import List, Set, Optional, Union
from functools import wraps
from fastapi import HTTPException, status, Depends
from backend.app.core.security import get_current_user
from backend.app.db.session import get_db, SessionLocal
from backend.app.db.models.user import User, UserRole, UserStatus


class Permission(str, Enum):
    API_KEYS_VIEW = "api_keys:view"
    API_KEYS_CREATE = "api_keys:create"
    API_KEYS_REVOKE = "api_keys:revoke"
    
    BILLING_VIEW = "billing:view"
    BILLING_EXPORT = "billing:export"
    BILLING_INVOICE = "billing:invoice"
    
    AUDIT_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"
    
    USERS_VIEW = "users:view"
    USERS_CREATE = "users:create"
    USERS_EDIT = "users:edit"
    USERS_DELETE = "users:delete"
    
    GUARDRAILS_VIEW = "guardrails:view"
    GUARDRAILS_EDIT = "guardrails:edit"
    GUARDRAILS_TEST = "guardrails:test"
    
    ROUTER_VIEW = "router:view"
    ROUTER_EDIT = "router:edit"
    
    GATEWAY_USE = "gateway:use"
    
    DASHBOARD_VIEW = "dashboard:view"
    
    SETTINGS_VIEW = "settings:view"
    SETTINGS_EDIT = "settings:edit"


ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        Permission.API_KEYS_VIEW,
        Permission.API_KEYS_CREATE,
        Permission.API_KEYS_REVOKE,
        Permission.BILLING_VIEW,
        Permission.BILLING_EXPORT,
        Permission.BILLING_INVOICE,
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
        Permission.USERS_VIEW,
        Permission.USERS_CREATE,
        Permission.USERS_EDIT,
        Permission.USERS_DELETE,
        Permission.GUARDRAILS_VIEW,
        Permission.GUARDRAILS_EDIT,
        Permission.GUARDRAILS_TEST,
        Permission.ROUTER_VIEW,
        Permission.ROUTER_EDIT,
        Permission.GATEWAY_USE,
        Permission.DASHBOARD_VIEW,
        Permission.SETTINGS_VIEW,
        Permission.SETTINGS_EDIT,
    },
    
    UserRole.MANAGER: {
        Permission.API_KEYS_VIEW,
        Permission.API_KEYS_CREATE,
        Permission.API_KEYS_REVOKE,
        Permission.BILLING_VIEW,
        Permission.BILLING_EXPORT,
        Permission.AUDIT_VIEW,
        Permission.USERS_VIEW,
        Permission.USERS_CREATE,
        Permission.USERS_EDIT,
        Permission.GUARDRAILS_VIEW,
        Permission.GUARDRAILS_EDIT,
        Permission.GUARDRAILS_TEST,
        Permission.ROUTER_VIEW,
        Permission.ROUTER_EDIT,
        Permission.GATEWAY_USE,
        Permission.DASHBOARD_VIEW,
        Permission.SETTINGS_VIEW,
        Permission.SETTINGS_EDIT,
    },
    
    UserRole.USER: {
        Permission.GATEWAY_USE,
        Permission.DASHBOARD_VIEW,
        Permission.API_KEYS_VIEW,
    },
    
    UserRole.VIEWER: {
        Permission.DASHBOARD_VIEW,
        Permission.BILLING_VIEW,
        Permission.AUDIT_VIEW,
        Permission.GUARDRAILS_VIEW,
        Permission.ROUTER_VIEW,
    },
}


def get_role_permissions(role: Union[UserRole, str]) -> Set[Permission]:
    if isinstance(role, str):
        try:
            role = UserRole(role)
        except ValueError:
            return set()
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: UserRole, permission: Permission) -> bool:
    return permission in get_role_permissions(role)


def get_user_from_token(token_data: dict, db) -> Optional[User]:
    from backend.app.db.models.tenant import Tenant
    
    tenant_id = int(token_data.get("sub", 0))
    email = token_data.get("email", "")
    
    user = db.query(User).filter(
        User.tenant_id == tenant_id,
        User.email == email,
        User.status == UserStatus.ACTIVE
    ).first()
    
    if user:
        return user
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant and tenant.email == email:
        existing_user = db.query(User).filter(
            User.tenant_id == tenant_id,
            User.email == email
        ).first()
        
        if existing_user:
            if existing_user.status != UserStatus.ACTIVE:
                return None
            return existing_user
        
        new_user = User(
            tenant_id=tenant_id,
            email=email,
            name=tenant.name,
            role=UserRole.ADMIN if tenant.is_admin else UserRole.MANAGER,
            status=UserStatus.ACTIVE
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    return None


class RequirePermission:
    def __init__(self, *permissions: Permission):
        self.required_permissions = set(permissions)
    
    async def __call__(
        self,
        current_user: dict = Depends(get_current_user),
    ):
        from backend.app.db.session import SessionLocal
        
        db = SessionLocal()
        try:
            user = get_user_from_token(current_user, db)
            
            if not user:
                if current_user.get("is_admin"):
                    user_role = UserRole.ADMIN
                else:
                    user_role = UserRole.MANAGER
            else:
                user_role = user.role
            
            user_permissions = get_role_permissions(user_role)
            
            if not self.required_permissions.issubset(user_permissions):
                missing = self.required_permissions - user_permissions
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {[p.value for p in missing]}"
                )
            
            return {
                **current_user,
                "role": user_role.value if isinstance(user_role, UserRole) else user_role,
                "permissions": [p.value for p in user_permissions],
                "user_id": user.id if user and hasattr(user, 'id') else None
            }
        finally:
            db.close()


def require_permission(*permissions: Permission):
    return Depends(RequirePermission(*permissions))


def require_any_permission(*permissions: Permission):
    class RequireAnyPermission:
        def __init__(self):
            self.required_permissions = set(permissions)
        
        async def __call__(
            self,
            current_user: dict = Depends(get_current_user),
        ):
            from backend.app.db.session import SessionLocal
            
            db = SessionLocal()
            try:
                user = get_user_from_token(current_user, db)
                
                if not user:
                    if current_user.get("is_admin"):
                        user_role = UserRole.ADMIN
                    else:
                        user_role = UserRole.MANAGER
                else:
                    user_role = user.role
                
                user_permissions = get_role_permissions(user_role)
                
                if not self.required_permissions.intersection(user_permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Need one of: {[p.value for p in self.required_permissions]}"
                    )
                
                return {
                    **current_user,
                    "role": user_role.value if isinstance(user_role, UserRole) else user_role,
                    "permissions": [p.value for p in user_permissions],
                    "user_id": user.id if user and hasattr(user, 'id') else None
                }
            finally:
                db.close()
    
    return Depends(RequireAnyPermission())


async def get_current_user_with_permissions(
    current_user: dict = Depends(get_current_user),
):
    from backend.app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        user = get_user_from_token(current_user, db)
        
        if not user:
            if current_user.get("is_admin"):
                user_role = UserRole.ADMIN
            else:
                user_role = UserRole.MANAGER
        else:
            user_role = user.role
        
        user_permissions = get_role_permissions(user_role)
        
        return {
            **current_user,
            "role": user_role.value if isinstance(user_role, UserRole) else user_role,
            "permissions": [p.value for p in user_permissions],
            "user_id": user.id if user and hasattr(user, 'id') else None
        }
    finally:
        db.close()
