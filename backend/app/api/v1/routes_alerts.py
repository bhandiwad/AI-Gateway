"""
Alert Configuration and Notification API

Endpoints for configuring alerts and viewing notifications.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from backend.app.db.session import get_db
from backend.app.core.security import get_current_tenant
from backend.app.core.permissions import require_permission, Permission
from backend.app.db.models import Tenant, User
from backend.app.db.models.alerts import (
    AlertConfig, AlertNotification, NotificationPreference,
    AlertType, AlertChannel, AlertSeverity
)
from backend.app.services.alert_service import alert_service

router = APIRouter()


# Pydantic Models
class AlertConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    alert_type: AlertType
    conditions: dict = Field(default_factory=dict)
    channels: List[AlertChannel]
    channel_config: dict = Field(default_factory=dict)
    cooldown_minutes: int = 15
    max_alerts_per_hour: int = 10
    severity: AlertSeverity = AlertSeverity.WARNING
    group_similar: bool = True


class AlertConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    conditions: Optional[dict] = None
    channels: Optional[List[AlertChannel]] = None
    channel_config: Optional[dict] = None
    cooldown_minutes: Optional[int] = None
    max_alerts_per_hour: Optional[int] = None
    severity: Optional[AlertSeverity] = None
    group_similar: Optional[bool] = None


class AlertConfigResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: Optional[str]
    is_active: bool
    alert_type: AlertType
    conditions: dict
    channels: List[str]
    channel_config: dict
    cooldown_minutes: int
    max_alerts_per_hour: int
    severity: AlertSeverity
    group_similar: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    context: dict
    channels_sent: List[str]
    is_read: bool
    is_acknowledged: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    slack_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    slack_user_id: Optional[str] = None
    alert_type_preferences: Optional[dict] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    enable_digest: Optional[bool] = None
    digest_frequency: Optional[str] = None


# Alert Config Endpoints

@router.get("/configs", response_model=List[AlertConfigResponse])
async def list_alert_configs(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.SETTINGS_VIEW)),
    db: Session = Depends(get_db)
):
    """List all alert configurations for the tenant."""
    configs = db.query(AlertConfig).filter(
        AlertConfig.tenant_id == tenant.id
    ).all()
    return configs


@router.post("/configs", response_model=AlertConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_config(
    config_data: AlertConfigCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.SETTINGS_EDIT)),
    db: Session = Depends(get_db)
):
    """Create a new alert configuration."""
    config = AlertConfig(
        tenant_id=tenant.id,
        name=config_data.name,
        description=config_data.description,
        alert_type=config_data.alert_type,
        conditions=config_data.conditions,
        channels=[c.value for c in config_data.channels],
        channel_config=config_data.channel_config,
        cooldown_minutes=config_data.cooldown_minutes,
        max_alerts_per_hour=config_data.max_alerts_per_hour,
        severity=config_data.severity,
        group_similar=config_data.group_similar,
        created_by=current_user.get("user_id")
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return config


@router.get("/configs/{config_id}", response_model=AlertConfigResponse)
async def get_alert_config(
    config_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.SETTINGS_VIEW)),
    db: Session = Depends(get_db)
):
    """Get a specific alert configuration."""
    config = db.query(AlertConfig).filter(
        AlertConfig.id == config_id,
        AlertConfig.tenant_id == tenant.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")
    
    return config


@router.put("/configs/{config_id}", response_model=AlertConfigResponse)
async def update_alert_config(
    config_id: int,
    config_data: AlertConfigUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.SETTINGS_EDIT)),
    db: Session = Depends(get_db)
):
    """Update an alert configuration."""
    config = db.query(AlertConfig).filter(
        AlertConfig.id == config_id,
        AlertConfig.tenant_id == tenant.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")
    
    update_data = config_data.model_dump(exclude_unset=True)
    
    # Convert channels enum to values
    if "channels" in update_data and update_data["channels"]:
        update_data["channels"] = [c.value for c in update_data["channels"]]
    
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    return config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_config(
    config_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.SETTINGS_EDIT)),
    db: Session = Depends(get_db)
):
    """Delete an alert configuration."""
    config = db.query(AlertConfig).filter(
        AlertConfig.id == config_id,
        AlertConfig.tenant_id == tenant.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")
    
    db.delete(config)
    db.commit()


# Notification Endpoints

@router.get("/notifications", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.DASHBOARD_VIEW)),
    db: Session = Depends(get_db)
):
    """List notifications for the tenant."""
    query = db.query(AlertNotification).filter(
        AlertNotification.tenant_id == tenant.id
    )
    
    if unread_only:
        query = query.filter(AlertNotification.is_read == False)
    
    notifications = query.order_by(
        AlertNotification.created_at.desc()
    ).limit(limit).all()
    
    return notifications


@router.get("/notifications/unread/count")
async def get_unread_count(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.DASHBOARD_VIEW)),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications."""
    count = db.query(AlertNotification).filter(
        AlertNotification.tenant_id == tenant.id,
        AlertNotification.is_read == False
    ).count()
    
    return {"unread_count": count}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.DASHBOARD_VIEW)),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notification = db.query(AlertNotification).filter(
        AlertNotification.id == notification_id,
        AlertNotification.tenant_id == tenant.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    alert_service.mark_as_read(db, notification_id, current_user.get("user_id"))
    
    return {"message": "Notification marked as read"}


@router.post("/notifications/{notification_id}/acknowledge")
async def acknowledge_notification(
    notification_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.DASHBOARD_VIEW)),
    db: Session = Depends(get_db)
):
    """Acknowledge a notification."""
    notification = db.query(AlertNotification).filter(
        AlertNotification.id == notification_id,
        AlertNotification.tenant_id == tenant.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    alert_service.acknowledge_alert(db, notification_id, current_user.get("user_id"))
    
    return {"message": "Notification acknowledged"}


@router.post("/notifications/mark-all-read")
async def mark_all_read(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.DASHBOARD_VIEW)),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read."""
    db.query(AlertNotification).filter(
        AlertNotification.tenant_id == tenant.id,
        AlertNotification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"message": "All notifications marked as read"}


# Test Alert Endpoint

@router.post("/test")
async def test_alert(
    alert_type: AlertType,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.SETTINGS_EDIT)),
    db: Session = Depends(get_db)
):
    """Send a test alert."""
    notification = await alert_service.trigger_alert(
        db=db,
        tenant_id=tenant.id,
        alert_type=alert_type,
        title=f"Test Alert: {alert_type.value}",
        message="This is a test alert to verify your alert configuration.",
        context={"test": True, "triggered_by": current_user.get("email", "admin")},
        severity=AlertSeverity.INFO
    )
    
    if notification:
        return {
            "message": "Test alert sent successfully",
            "notification_id": notification.id,
            "channels_sent": notification.channels_sent
        }
    else:
        return {
            "message": "No alert configs found or alert was throttled",
            "notification_id": None
        }


# User Notification Preferences

@router.get("/preferences")
async def get_notification_preferences(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.DASHBOARD_VIEW)),
    db: Session = Depends(get_db)
):
    """Get user's notification preferences."""
    user_id = current_user.get("user_id")
    
    prefs = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()
    
    if not prefs:
        # Create default preferences
        prefs = NotificationPreference(
            user_id=user_id,
            tenant_id=tenant.id
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return prefs


@router.put("/preferences")
async def update_notification_preferences(
    prefs_data: NotificationPreferenceUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: dict = Depends(require_permission(Permission.DASHBOARD_VIEW)),
    db: Session = Depends(get_db)
):
    """Update user's notification preferences."""
    user_id = current_user.get("user_id")
    
    prefs = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()
    
    if not prefs:
        prefs = NotificationPreference(
            user_id=user_id,
            tenant_id=tenant.id
        )
        db.add(prefs)
    
    update_data = prefs_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    
    return prefs
