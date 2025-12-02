from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import io

from backend.app.db.session import get_db
from backend.app.core.security import get_current_tenant, get_current_user
from backend.app.core.permissions import Permission, RequirePermission
from backend.app.db.models.tenant import Tenant
from backend.app.services.billing_service import billing_service
from backend.app.services.audit_service import audit_service
from backend.app.db.models.audit_log import AuditAction
from backend.app.schemas.billing import (
    TenantBillingReport, Invoice, CostForecast,
    BillingReportRequest, InvoiceRequest
)

router = APIRouter()


@router.get("/billing/summary")
async def get_billing_summary(
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: dict = Depends(RequirePermission(Permission.BILLING_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    summary = billing_service.get_tenant_billing_summary(
        db=db,
        tenant_id=tenant.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return summary


@router.get("/billing/user/{user_id}")
async def get_user_billing(
    user_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: dict = Depends(RequirePermission(Permission.BILLING_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    details = billing_service.get_user_billing_details(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not details:
        raise HTTPException(status_code=404, detail="User not found")
    
    return details


@router.post("/billing/invoice")
async def generate_invoice(
    request: InvoiceRequest,
    current_user: dict = Depends(RequirePermission(Permission.BILLING_INVOICE)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    invoice = billing_service.generate_invoice(
        db=db,
        tenant_id=tenant.id,
        start_date=request.start_date,
        end_date=request.end_date,
        user_rate=request.user_rate,
        include_token_costs=request.include_token_costs
    )
    
    audit_service.log(
        db=db,
        tenant_id=tenant.id,
        action=AuditAction.DATA_EXPORT,
        description=f"Generated invoice {invoice['invoice_number']}",
        metadata={
            "invoice_number": invoice["invoice_number"],
            "total": invoice["total"]
        }
    )
    
    return invoice


@router.get("/billing/export/csv")
async def export_usage_csv(
    start_date: datetime,
    end_date: datetime,
    include_user_details: bool = True,
    current_user: dict = Depends(RequirePermission(Permission.BILLING_EXPORT)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    csv_content = billing_service.export_usage_csv(
        db=db,
        tenant_id=tenant.id,
        start_date=start_date,
        end_date=end_date,
        include_user_details=include_user_details
    )
    
    audit_service.log(
        db=db,
        tenant_id=tenant.id,
        action=AuditAction.DATA_EXPORT,
        description="Exported usage data to CSV",
        metadata={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    )
    
    return StreamingResponse(
        io.BytesIO(csv_content.encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=usage_{tenant.id}_{start_date.strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/billing/forecast", response_model=CostForecast)
async def get_cost_forecast(
    days: int = Query(30, ge=7, le=90),
    current_user: dict = Depends(RequirePermission(Permission.BILLING_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    forecast = billing_service.get_cost_forecast(
        db=db,
        tenant_id=tenant.id,
        days_to_forecast=days
    )
    
    return forecast


@router.get("/billing/models")
async def get_model_costs(
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: dict = Depends(RequirePermission(Permission.BILLING_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    summary = billing_service.get_tenant_billing_summary(
        db=db,
        tenant_id=tenant.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "models": summary["by_model"]
    }


@router.get("/billing/users")
async def get_user_costs(
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: dict = Depends(RequirePermission(Permission.BILLING_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    summary = billing_service.get_tenant_billing_summary(
        db=db,
        tenant_id=tenant.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "active_users": summary["summary"]["active_users"],
        "users": summary["by_user"]
    }
