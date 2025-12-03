from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException

from backend.app.db.models import Tenant, APIKey
from backend.app.db.models.provider_config import EnhancedProviderConfig, GuardrailProfile
from backend.app.core.security import get_password_hash, verify_password, generate_api_key, hash_api_key
from backend.app.schemas.tenant import TenantCreate, TenantUpdate
from backend.app.schemas.api_key import APIKeyCreate


class TenancyService:
    def _validate_resource_ownership(
        self, 
        db: Session, 
        tenant_id: int, 
        guardrail_profile_id: Optional[int] = None,
        default_provider_id: Optional[int] = None
    ) -> None:
        """Validate that referenced resources belong to the same tenant or are global."""
        if guardrail_profile_id:
            profile = db.query(GuardrailProfile).filter(
                GuardrailProfile.id == guardrail_profile_id
            ).first()
            if profile and profile.tenant_id is not None and profile.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot reference guardrail profile from another tenant"
                )
        
        if default_provider_id:
            provider = db.query(EnhancedProviderConfig).filter(
                EnhancedProviderConfig.id == default_provider_id
            ).first()
            if provider and provider.tenant_id is not None and provider.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot reference provider from another tenant"
                )
    
    def get_tenant_by_email(self, db: Session, email: str) -> Optional[Tenant]:
        return db.query(Tenant).filter(Tenant.email == email).first()
    
    def get_tenant_by_id(self, db: Session, tenant_id: int) -> Optional[Tenant]:
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    def get_tenants(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Tenant]:
        return db.query(Tenant).offset(skip).limit(limit).all()
    
    def create_tenant(self, db: Session, tenant: TenantCreate) -> Tenant:
        db_tenant = Tenant(
            name=tenant.name,
            email=tenant.email,
            password_hash=get_password_hash(tenant.password),
            allowed_models=[]
        )
        db.add(db_tenant)
        db.commit()
        db.refresh(db_tenant)
        return db_tenant
    
    def update_tenant(
        self, 
        db: Session, 
        tenant_id: int, 
        tenant_update: TenantUpdate
    ) -> Optional[Tenant]:
        db_tenant = self.get_tenant_by_id(db, tenant_id)
        if not db_tenant:
            return None
        
        update_data = tenant_update.model_dump(exclude_unset=True)
        
        self._validate_resource_ownership(
            db, 
            tenant_id,
            guardrail_profile_id=update_data.get('guardrail_profile_id'),
            default_provider_id=update_data.get('default_provider_id')
        )
        
        for field, value in update_data.items():
            setattr(db_tenant, field, value)
        
        db.commit()
        db.refresh(db_tenant)
        return db_tenant
    
    def authenticate_tenant(
        self, 
        db: Session, 
        email: str, 
        password: str
    ) -> Optional[Tenant]:
        tenant = self.get_tenant_by_email(db, email)
        if not tenant:
            return None
        if not verify_password(password, tenant.password_hash):
            return None
        return tenant
    
    def get_api_key_by_hash(self, db: Session, key_hash: str) -> Optional[APIKey]:
        return db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
    
    def get_tenant_api_keys(self, db: Session, tenant_id: int) -> List[APIKey]:
        return db.query(APIKey).filter(APIKey.tenant_id == tenant_id).all()
    
    def create_api_key(
        self, 
        db: Session, 
        tenant_id: int, 
        api_key_data: APIKeyCreate
    ) -> tuple[APIKey, str]:
        self._validate_resource_ownership(
            db, 
            tenant_id,
            guardrail_profile_id=getattr(api_key_data, 'guardrail_profile_id', None),
            default_provider_id=getattr(api_key_data, 'default_provider_id', None)
        )
        
        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key)
        
        db_key = APIKey(
            tenant_id=tenant_id,
            name=api_key_data.name,
            key_hash=key_hash,
            key_prefix=raw_key[:12],
            environment=getattr(api_key_data, 'environment', 'production'),
            guardrail_profile_id=getattr(api_key_data, 'guardrail_profile_id', None),
            default_provider_id=getattr(api_key_data, 'default_provider_id', None),
            rate_limit_override=api_key_data.rate_limit_override,
            allowed_models_override=api_key_data.allowed_models_override,
            allowed_providers_override=getattr(api_key_data, 'allowed_providers_override', None),
            cost_limit_daily=getattr(api_key_data, 'cost_limit_daily', None),
            cost_limit_monthly=getattr(api_key_data, 'cost_limit_monthly', None),
            expires_at=api_key_data.expires_at
        )
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        
        return db_key, raw_key
    
    def revoke_api_key(self, db: Session, key_id: int, tenant_id: int) -> bool:
        db_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.tenant_id == tenant_id
        ).first()
        
        if not db_key:
            return False
        
        db_key.is_active = False
        db.commit()
        return True
    
    def validate_api_key(self, db: Session, api_key: str) -> Optional[tuple[Tenant, APIKey]]:
        key_hash = hash_api_key(api_key)
        db_key = self.get_api_key_by_hash(db, key_hash)
        
        if not db_key:
            return None
        
        if db_key.expires_at and db_key.expires_at < datetime.utcnow():
            return None
        
        tenant = self.get_tenant_by_id(db, db_key.tenant_id)
        if not tenant or not tenant.is_active:
            return None
        
        db_key.last_used_at = datetime.utcnow()
        db.commit()
        
        return tenant, db_key
    
    def update_tenant_spend(
        self, 
        db: Session, 
        tenant_id: int, 
        cost: float
    ) -> None:
        tenant = self.get_tenant_by_id(db, tenant_id)
        if tenant:
            tenant.current_spend = (tenant.current_spend or 0) + cost
            db.commit()


tenancy_service = TenancyService()
