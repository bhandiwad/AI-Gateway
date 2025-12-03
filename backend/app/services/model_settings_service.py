from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import yaml
import os

from backend.app.db.models.tenant_model_settings import TenantModelSettings


class ModelSettingsService:
    def __init__(self):
        self._models_cache = None
    
    def _load_models_from_yaml(self) -> List[Dict[str, Any]]:
        if self._models_cache:
            return self._models_cache
        
        config_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'configs', 'models.yaml'
        )
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self._models_cache = config.get("models", [])
                return self._models_cache
        except Exception:
            return []
    
    def get_models_for_tenant(
        self, 
        db: Session, 
        tenant_id: int
    ) -> List[Dict[str, Any]]:
        base_models = self._load_models_from_yaml()
        
        settings = db.query(TenantModelSettings).filter(
            TenantModelSettings.tenant_id == tenant_id
        ).all()
        
        settings_map = {s.model_id: s for s in settings}
        
        result = []
        for idx, model in enumerate(base_models):
            model_id = model.get("id")
            setting = settings_map.get(model_id)
            
            result.append({
                **model,
                "is_enabled": setting.is_enabled if setting else True,
                "display_order": setting.display_order if setting else idx,
                "has_custom_settings": setting is not None
            })
        
        result.sort(key=lambda x: x["display_order"])
        return result
    
    def update_model_settings(
        self,
        db: Session,
        tenant_id: int,
        model_id: str,
        is_enabled: Optional[bool] = None,
        display_order: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        base_models = self._load_models_from_yaml()
        model_ids = [m["id"] for m in base_models]
        
        if model_id not in model_ids:
            return None
        
        setting = db.query(TenantModelSettings).filter(
            and_(
                TenantModelSettings.tenant_id == tenant_id,
                TenantModelSettings.model_id == model_id
            )
        ).first()
        
        if not setting:
            setting = TenantModelSettings(
                tenant_id=tenant_id,
                model_id=model_id,
                is_enabled=is_enabled if is_enabled is not None else True,
                display_order=display_order if display_order is not None else 0
            )
            db.add(setting)
        else:
            if is_enabled is not None:
                setting.is_enabled = is_enabled
            if display_order is not None:
                setting.display_order = display_order
        
        db.commit()
        db.refresh(setting)
        
        base_model = next((m for m in base_models if m["id"] == model_id), {})
        return {
            **base_model,
            "is_enabled": setting.is_enabled,
            "display_order": setting.display_order,
            "has_custom_settings": True
        }
    
    def reorder_models(
        self,
        db: Session,
        tenant_id: int,
        model_order: List[str]
    ) -> List[Dict[str, Any]]:
        base_models = self._load_models_from_yaml()
        valid_model_ids = [m["id"] for m in base_models]
        
        for idx, model_id in enumerate(model_order):
            if model_id not in valid_model_ids:
                continue
                
            setting = db.query(TenantModelSettings).filter(
                and_(
                    TenantModelSettings.tenant_id == tenant_id,
                    TenantModelSettings.model_id == model_id
                )
            ).first()
            
            if not setting:
                setting = TenantModelSettings(
                    tenant_id=tenant_id,
                    model_id=model_id,
                    is_enabled=True,
                    display_order=idx
                )
                db.add(setting)
            else:
                setting.display_order = idx
        
        db.commit()
        return self.get_models_for_tenant(db, tenant_id)
    
    def toggle_model(
        self,
        db: Session,
        tenant_id: int,
        model_id: str,
        is_enabled: bool
    ) -> Optional[Dict[str, Any]]:
        return self.update_model_settings(
            db, tenant_id, model_id, is_enabled=is_enabled
        )
    
    def get_enabled_models(
        self,
        db: Session,
        tenant_id: int
    ) -> List[str]:
        models = self.get_models_for_tenant(db, tenant_id)
        return [m["id"] for m in models if m["is_enabled"]]


model_settings_service = ModelSettingsService()
