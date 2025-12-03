from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import yaml
import os

from backend.app.db.models.tenant_model_settings import TenantModelSettings
from backend.app.db.models.custom_model import CustomModel


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
    
    def _get_custom_models(self, db: Session, tenant_id: int) -> List[Dict[str, Any]]:
        custom_models = db.query(CustomModel).filter(
            CustomModel.tenant_id == tenant_id
        ).all()
        
        return [
            {
                "id": cm.model_id,
                "name": cm.name,
                "provider": cm.provider,
                "context_length": cm.context_length,
                "input_cost_per_1k": cm.input_cost_per_1k,
                "output_cost_per_1k": cm.output_cost_per_1k,
                "supports_streaming": cm.supports_streaming,
                "supports_functions": cm.supports_functions,
                "supports_vision": cm.supports_vision,
                "api_base_url": cm.api_base_url,
                "api_key_name": cm.api_key_name,
                "is_enabled": cm.is_enabled,
                "display_order": cm.display_order,
                "is_custom": True,
                "custom_model_id": cm.id
            }
            for cm in custom_models
        ]
    
    def get_models_for_tenant(
        self, 
        db: Session, 
        tenant_id: int
    ) -> List[Dict[str, Any]]:
        base_models = self._load_models_from_yaml()
        custom_models = self._get_custom_models(db, tenant_id)
        
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
                "has_custom_settings": setting is not None,
                "is_custom": False
            })
        
        result.extend(custom_models)
        result.sort(key=lambda x: x["display_order"])
        return result
    
    def create_custom_model(
        self,
        db: Session,
        tenant_id: int,
        model_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        existing = db.query(CustomModel).filter(
            and_(
                CustomModel.tenant_id == tenant_id,
                CustomModel.model_id == model_data.get("model_id")
            )
        ).first()
        
        if existing:
            raise ValueError(f"Model with ID '{model_data.get('model_id')}' already exists")
        
        max_order = db.query(CustomModel).filter(
            CustomModel.tenant_id == tenant_id
        ).count() + 1000
        
        custom_model = CustomModel(
            tenant_id=tenant_id,
            model_id=model_data.get("model_id"),
            name=model_data.get("name"),
            provider=model_data.get("provider", "custom"),
            context_length=model_data.get("context_length", 128000),
            input_cost_per_1k=model_data.get("input_cost_per_1k", 0.0),
            output_cost_per_1k=model_data.get("output_cost_per_1k", 0.0),
            supports_streaming=model_data.get("supports_streaming", True),
            supports_functions=model_data.get("supports_functions", False),
            supports_vision=model_data.get("supports_vision", False),
            api_base_url=model_data.get("api_base_url"),
            api_key_name=model_data.get("api_key_name"),
            is_enabled=model_data.get("is_enabled", True),
            display_order=max_order
        )
        
        db.add(custom_model)
        db.commit()
        db.refresh(custom_model)
        
        return {
            "id": custom_model.model_id,
            "name": custom_model.name,
            "provider": custom_model.provider,
            "context_length": custom_model.context_length,
            "input_cost_per_1k": custom_model.input_cost_per_1k,
            "output_cost_per_1k": custom_model.output_cost_per_1k,
            "supports_streaming": custom_model.supports_streaming,
            "supports_functions": custom_model.supports_functions,
            "supports_vision": custom_model.supports_vision,
            "api_base_url": custom_model.api_base_url,
            "api_key_name": custom_model.api_key_name,
            "is_enabled": custom_model.is_enabled,
            "display_order": custom_model.display_order,
            "is_custom": True,
            "custom_model_id": custom_model.id
        }
    
    def update_custom_model(
        self,
        db: Session,
        tenant_id: int,
        model_id: str,
        model_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        custom_model = db.query(CustomModel).filter(
            and_(
                CustomModel.tenant_id == tenant_id,
                CustomModel.model_id == model_id
            )
        ).first()
        
        if not custom_model:
            return None
        
        if "name" in model_data:
            custom_model.name = model_data["name"]
        if "provider" in model_data:
            custom_model.provider = model_data["provider"]
        if "context_length" in model_data:
            custom_model.context_length = model_data["context_length"]
        if "input_cost_per_1k" in model_data:
            custom_model.input_cost_per_1k = model_data["input_cost_per_1k"]
        if "output_cost_per_1k" in model_data:
            custom_model.output_cost_per_1k = model_data["output_cost_per_1k"]
        if "supports_streaming" in model_data:
            custom_model.supports_streaming = model_data["supports_streaming"]
        if "supports_functions" in model_data:
            custom_model.supports_functions = model_data["supports_functions"]
        if "supports_vision" in model_data:
            custom_model.supports_vision = model_data["supports_vision"]
        if "api_base_url" in model_data:
            custom_model.api_base_url = model_data["api_base_url"]
        if "api_key_name" in model_data:
            custom_model.api_key_name = model_data["api_key_name"]
        if "is_enabled" in model_data:
            custom_model.is_enabled = model_data["is_enabled"]
        
        db.commit()
        db.refresh(custom_model)
        
        return {
            "id": custom_model.model_id,
            "name": custom_model.name,
            "provider": custom_model.provider,
            "context_length": custom_model.context_length,
            "input_cost_per_1k": custom_model.input_cost_per_1k,
            "output_cost_per_1k": custom_model.output_cost_per_1k,
            "supports_streaming": custom_model.supports_streaming,
            "supports_functions": custom_model.supports_functions,
            "supports_vision": custom_model.supports_vision,
            "api_base_url": custom_model.api_base_url,
            "api_key_name": custom_model.api_key_name,
            "is_enabled": custom_model.is_enabled,
            "display_order": custom_model.display_order,
            "is_custom": True,
            "custom_model_id": custom_model.id
        }
    
    def delete_custom_model(
        self,
        db: Session,
        tenant_id: int,
        model_id: str
    ) -> bool:
        custom_model = db.query(CustomModel).filter(
            and_(
                CustomModel.tenant_id == tenant_id,
                CustomModel.model_id == model_id
            )
        ).first()
        
        if not custom_model:
            return False
        
        db.delete(custom_model)
        db.commit()
        return True
    
    def update_model_settings(
        self,
        db: Session,
        tenant_id: int,
        model_id: str,
        is_enabled: Optional[bool] = None,
        display_order: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        custom_model = db.query(CustomModel).filter(
            and_(
                CustomModel.tenant_id == tenant_id,
                CustomModel.model_id == model_id
            )
        ).first()
        
        if custom_model:
            if is_enabled is not None:
                custom_model.is_enabled = is_enabled
            if display_order is not None:
                custom_model.display_order = display_order
            db.commit()
            db.refresh(custom_model)
            return {
                "id": custom_model.model_id,
                "name": custom_model.name,
                "provider": custom_model.provider,
                "is_enabled": custom_model.is_enabled,
                "display_order": custom_model.display_order,
                "is_custom": True
            }
        
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
            "has_custom_settings": True,
            "is_custom": False
        }
    
    def reorder_models(
        self,
        db: Session,
        tenant_id: int,
        model_order: List[str]
    ) -> List[Dict[str, Any]]:
        base_models = self._load_models_from_yaml()
        valid_model_ids = [m["id"] for m in base_models]
        
        custom_models = db.query(CustomModel).filter(
            CustomModel.tenant_id == tenant_id
        ).all()
        custom_model_ids = [cm.model_id for cm in custom_models]
        
        for idx, model_id in enumerate(model_order):
            if model_id in custom_model_ids:
                cm = next(c for c in custom_models if c.model_id == model_id)
                cm.display_order = idx
            elif model_id in valid_model_ids:
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
