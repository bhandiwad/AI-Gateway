from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from backend.app.db.models.custom_guardrail_policy import CustomGuardrailPolicy


DEFAULT_POLICY_CONFIG = {
    "pii_detection": {
        "enabled": True,
        "patterns": ["ssn", "credit_card", "bank_account", "aadhaar", "pan"],
        "action": "redact"
    },
    "toxicity_filter": {
        "enabled": True,
        "threshold": 0.7,
        "action": "block"
    },
    "prompt_injection": {
        "enabled": True,
        "action": "block"
    },
    "jailbreak_detection": {
        "enabled": True,
        "action": "block"
    },
    "financial_advice": {
        "enabled": False,
        "action": "warn"
    },
    "max_tokens": {
        "enabled": True,
        "limit": 4096
    },
    "allowed_topics": [],
    "blocked_topics": []
}


class CustomPolicyService:
    
    def get_tenant_policies(
        self,
        db: Session,
        tenant_id: int
    ) -> List[Dict[str, Any]]:
        policies = db.query(CustomGuardrailPolicy).filter(
            CustomGuardrailPolicy.tenant_id == tenant_id
        ).order_by(CustomGuardrailPolicy.priority.desc()).all()
        
        return [self._policy_to_dict(p) for p in policies]
    
    def get_policy_by_id(
        self,
        db: Session,
        tenant_id: int,
        policy_id: int
    ) -> Optional[Dict[str, Any]]:
        policy = db.query(CustomGuardrailPolicy).filter(
            and_(
                CustomGuardrailPolicy.id == policy_id,
                CustomGuardrailPolicy.tenant_id == tenant_id
            )
        ).first()
        
        return self._policy_to_dict(policy) if policy else None
    
    def create_policy(
        self,
        db: Session,
        tenant_id: int,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        policy_config = {**DEFAULT_POLICY_CONFIG}
        if config:
            for key, value in config.items():
                if key in policy_config:
                    if isinstance(policy_config[key], dict) and isinstance(value, dict):
                        policy_config[key].update(value)
                    else:
                        policy_config[key] = value
                else:
                    policy_config[key] = value
        
        policy = CustomGuardrailPolicy(
            tenant_id=tenant_id,
            name=name,
            description=description,
            policy_type="custom",
            is_active=is_active,
            config=policy_config,
            created_by=created_by
        )
        
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        return self._policy_to_dict(policy)
    
    def update_policy(
        self,
        db: Session,
        tenant_id: int,
        policy_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        policy = db.query(CustomGuardrailPolicy).filter(
            and_(
                CustomGuardrailPolicy.id == policy_id,
                CustomGuardrailPolicy.tenant_id == tenant_id
            )
        ).first()
        
        if not policy:
            return None
        
        if name is not None:
            policy.name = name
        if description is not None:
            policy.description = description
        if is_active is not None:
            policy.is_active = is_active
        if config is not None:
            existing_config = policy.config or {}
            for key, value in config.items():
                if key in existing_config and isinstance(existing_config[key], dict) and isinstance(value, dict):
                    existing_config[key].update(value)
                else:
                    existing_config[key] = value
            policy.config = existing_config
        
        policy.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(policy)
        
        return self._policy_to_dict(policy)
    
    def delete_policy(
        self,
        db: Session,
        tenant_id: int,
        policy_id: int
    ) -> bool:
        policy = db.query(CustomGuardrailPolicy).filter(
            and_(
                CustomGuardrailPolicy.id == policy_id,
                CustomGuardrailPolicy.tenant_id == tenant_id
            )
        ).first()
        
        if not policy:
            return False
        
        db.delete(policy)
        db.commit()
        return True
    
    def set_default_policy(
        self,
        db: Session,
        tenant_id: int,
        policy_id: int
    ) -> Optional[Dict[str, Any]]:
        db.query(CustomGuardrailPolicy).filter(
            CustomGuardrailPolicy.tenant_id == tenant_id
        ).update({"is_default": False})
        
        policy = db.query(CustomGuardrailPolicy).filter(
            and_(
                CustomGuardrailPolicy.id == policy_id,
                CustomGuardrailPolicy.tenant_id == tenant_id
            )
        ).first()
        
        if not policy:
            db.rollback()
            return None
        
        policy.is_default = True
        db.commit()
        db.refresh(policy)
        
        return self._policy_to_dict(policy)
    
    def _policy_to_dict(self, policy: CustomGuardrailPolicy) -> Dict[str, Any]:
        return {
            "id": policy.id,
            "tenant_id": policy.tenant_id,
            "name": policy.name,
            "description": policy.description,
            "policy_type": policy.policy_type,
            "is_active": policy.is_active,
            "is_default": policy.is_default,
            "priority": policy.priority,
            "config": policy.config,
            "created_by": policy.created_by,
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
        }


custom_policy_service = CustomPolicyService()
