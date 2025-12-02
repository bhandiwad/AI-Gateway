from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import io

from backend.app.db.session import get_db
from backend.app.core.security import get_current_tenant
from backend.app.db.models.tenant import Tenant
from backend.app.db.models.audit_log import AuditAction, AuditSeverity
from backend.app.services.audit_service import audit_service
from backend.app.schemas.audit import (
    AuditLogResponse, AuditSummary, AuditExportRequest
)

router = APIRouter()


@router.get("/audit/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    action_filter = AuditAction(action) if action else None
    severity_filter = AuditSeverity(severity) if severity else None
    
    logs = audit_service.get_audit_logs(
        db=db,
        tenant_id=tenant.id,
        user_id=user_id,
        action=action_filter,
        severity=severity_filter,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    return [
        AuditLogResponse(
            id=log.id,
            tenant_id=log.tenant_id,
            user_id=log.user_id,
            action=log.action.value,
            severity=log.severity.value,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            description=log.description,
            request_id=log.request_id,
            ip_address=log.ip_address,
            created_at=log.created_at,
            metadata=log.metadata_
        )
        for log in logs
    ]


@router.get("/audit/summary", response_model=AuditSummary)
async def get_audit_summary(
    days: int = Query(30, ge=1, le=365),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    summary = audit_service.get_audit_summary(db, tenant.id, days)
    return summary


@router.get("/audit/actions")
async def get_audit_actions():
    return {
        "actions": [action.value for action in AuditAction],
        "severities": [severity.value for severity in AuditSeverity]
    }


@router.post("/audit/export")
async def export_audit_logs(
    request: AuditExportRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    logs = audit_service.export_audit_logs(
        db=db,
        tenant_id=tenant.id,
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    audit_service.log(
        db=db,
        tenant_id=tenant.id,
        action=AuditAction.DATA_EXPORT,
        description=f"Exported {len(logs)} audit logs",
        metadata={
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "count": len(logs)
        }
    )
    
    return {
        "logs": logs,
        "total_count": len(logs),
        "export_date": datetime.utcnow().isoformat()
    }


@router.get("/audit/export/json")
async def export_audit_logs_json(
    start_date: datetime,
    end_date: datetime,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    logs = audit_service.export_audit_logs(
        db=db,
        tenant_id=tenant.id,
        start_date=start_date,
        end_date=end_date
    )
    
    json_content = json.dumps({
        "tenant_id": tenant.id,
        "export_date": datetime.utcnow().isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "logs": logs
    }, indent=2)
    
    return StreamingResponse(
        io.BytesIO(json_content.encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{tenant.id}_{start_date.strftime('%Y%m%d')}.json"
        }
    )


@router.get("/audit/security-events")
async def get_security_events(
    days: int = Query(7, ge=1, le=90),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    security_actions = [
        AuditAction.LOGIN_FAILED,
        AuditAction.GUARDRAIL_TRIGGERED,
        AuditAction.RATE_LIMIT_HIT,
        AuditAction.BUDGET_EXCEEDED
    ]
    
    events = []
    for action in security_actions:
        action_events = audit_service.get_audit_logs(
            db=db,
            tenant_id=tenant.id,
            action=action,
            start_date=start_date,
            limit=100
        )
        events.extend(action_events)
    
    events.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "period_days": days,
        "total_events": len(events),
        "events": [
            {
                "id": e.id,
                "action": e.action.value,
                "severity": e.severity.value,
                "description": e.description,
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat()
            }
            for e in events[:100]
        ]
    }
