from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import csv
import io

from backend.app.db.models.usage_log import UsageLog
from backend.app.db.models.user import User, UserStatus
from backend.app.db.models.tenant import Tenant


class BillingService:
    def get_tenant_billing_summary(
        self,
        db: Session,
        tenant_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        active_users = db.query(func.count(User.id)).filter(
            User.tenant_id == tenant_id,
            User.status == UserStatus.ACTIVE
        ).scalar() or 0
        
        usage_stats = db.query(
            func.count(UsageLog.id).label('total_requests'),
            func.coalesce(func.sum(UsageLog.total_tokens), 0).label('total_tokens'),
            func.coalesce(func.sum(UsageLog.cost), 0.0).label('total_cost')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at <= end_date
        ).first()
        
        by_model = db.query(
            UsageLog.model,
            UsageLog.provider,
            func.count(UsageLog.id).label('requests'),
            func.coalesce(func.sum(UsageLog.prompt_tokens), 0).label('prompt_tokens'),
            func.coalesce(func.sum(UsageLog.completion_tokens), 0).label('completion_tokens'),
            func.coalesce(func.sum(UsageLog.cost), 0.0).label('cost')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at <= end_date
        ).group_by(UsageLog.model, UsageLog.provider).all()
        
        by_user = db.query(
            User.id,
            User.name,
            User.email,
            func.count(UsageLog.id).label('requests'),
            func.coalesce(func.sum(UsageLog.total_tokens), 0).label('tokens'),
            func.coalesce(func.sum(UsageLog.cost), 0.0).label('cost')
        ).join(UsageLog, UsageLog.user_id == User.id).filter(
            User.tenant_id == tenant_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at <= end_date
        ).group_by(User.id, User.name, User.email).all()
        
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name if tenant else "Unknown",
            "billing_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "active_users": active_users,
                "total_requests": usage_stats.total_requests or 0,
                "total_tokens": int(usage_stats.total_tokens or 0),
                "token_cost": float(usage_stats.total_cost or 0),
            },
            "by_model": [
                {
                    "model": m.model,
                    "provider": m.provider,
                    "requests": m.requests,
                    "prompt_tokens": int(m.prompt_tokens or 0),
                    "completion_tokens": int(m.completion_tokens or 0),
                    "cost": float(m.cost or 0)
                }
                for m in by_model
            ],
            "by_user": [
                {
                    "user_id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "requests": u.requests,
                    "tokens": int(u.tokens or 0),
                    "cost": float(u.cost or 0)
                }
                for u in by_user
            ]
        }

    def get_user_billing_details(
        self,
        db: Session,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        usage_stats = db.query(
            func.count(UsageLog.id).label('total_requests'),
            func.coalesce(func.sum(UsageLog.total_tokens), 0).label('total_tokens'),
            func.coalesce(func.sum(UsageLog.cost), 0.0).label('total_cost'),
            func.coalesce(func.avg(UsageLog.latency_ms), 0.0).label('avg_latency')
        ).filter(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at <= end_date
        ).first()
        
        by_model = db.query(
            UsageLog.model,
            func.count(UsageLog.id).label('requests'),
            func.coalesce(func.sum(UsageLog.total_tokens), 0).label('tokens'),
            func.coalesce(func.sum(UsageLog.cost), 0.0).label('cost')
        ).filter(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at <= end_date
        ).group_by(UsageLog.model).all()
        
        daily_usage = db.query(
            func.date_trunc('day', UsageLog.created_at).label('date'),
            func.count(UsageLog.id).label('requests'),
            func.coalesce(func.sum(UsageLog.total_tokens), 0).label('tokens'),
            func.coalesce(func.sum(UsageLog.cost), 0.0).label('cost')
        ).filter(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at <= end_date
        ).group_by(func.date_trunc('day', UsageLog.created_at)).order_by(
            func.date_trunc('day', UsageLog.created_at)
        ).all()
        
        return {
            "user_id": user_id,
            "user_name": user.name,
            "user_email": user.email,
            "billing_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_requests": usage_stats.total_requests or 0,
                "total_tokens": int(usage_stats.total_tokens or 0),
                "total_cost": float(usage_stats.total_cost or 0),
                "avg_latency_ms": float(usage_stats.avg_latency or 0),
                "budget_limit": user.monthly_budget,
                "budget_used_percent": (
                    (usage_stats.total_cost or 0) / user.monthly_budget * 100
                    if user.monthly_budget > 0 else 0
                )
            },
            "by_model": [
                {
                    "model": m.model,
                    "requests": m.requests,
                    "tokens": int(m.tokens or 0),
                    "cost": float(m.cost or 0)
                }
                for m in by_model
            ],
            "daily_usage": [
                {
                    "date": d.date.isoformat() if d.date else None,
                    "requests": d.requests,
                    "tokens": int(d.tokens or 0),
                    "cost": float(d.cost or 0)
                }
                for d in daily_usage
            ]
        }

    def generate_invoice(
        self,
        db: Session,
        tenant_id: int,
        start_date: datetime,
        end_date: datetime,
        user_rate: float = 10.0,
        include_token_costs: bool = True
    ) -> Dict[str, Any]:
        billing_summary = self.get_tenant_billing_summary(
            db, tenant_id, start_date, end_date
        )
        
        active_users = billing_summary["summary"]["active_users"]
        user_fee = active_users * user_rate
        
        token_cost = billing_summary["summary"]["token_cost"] if include_token_costs else 0
        
        subtotal = user_fee + token_cost
        tax_rate = 0.0
        tax = subtotal * tax_rate
        total = subtotal + tax
        
        return {
            "invoice_number": f"INV-{tenant_id}-{start_date.strftime('%Y%m')}",
            "tenant_id": tenant_id,
            "tenant_name": billing_summary["tenant_name"],
            "billing_period": billing_summary["billing_period"],
            "generated_at": datetime.utcnow().isoformat(),
            "line_items": [
                {
                    "description": f"Active Users ({active_users} users @ ${user_rate}/user)",
                    "quantity": active_users,
                    "unit_price": user_rate,
                    "amount": user_fee
                },
                {
                    "description": f"Token Usage ({billing_summary['summary']['total_tokens']:,} tokens)",
                    "quantity": billing_summary["summary"]["total_tokens"],
                    "unit_price": None,
                    "amount": token_cost
                }
            ],
            "model_breakdown": billing_summary["by_model"],
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "tax": tax,
            "total": total,
            "currency": "USD"
        }

    def export_usage_csv(
        self,
        db: Session,
        tenant_id: int,
        start_date: datetime,
        end_date: datetime,
        include_user_details: bool = True
    ) -> str:
        query = db.query(UsageLog).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at <= end_date
        ).order_by(UsageLog.created_at)
        
        if include_user_details:
            query = query.join(User, UsageLog.user_id == User.id, isouter=True)
        
        logs = query.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = [
            "request_id", "timestamp", "user_id",
            "model", "provider", "prompt_tokens", "completion_tokens",
            "total_tokens", "cost", "latency_ms", "status",
            "guardrail_triggered"
        ]
        writer.writerow(headers)
        
        for log in logs:
            cost_val = log.cost if log.cost is not None else 0.0
            writer.writerow([
                log.request_id,
                log.created_at.isoformat(),
                log.user_id or "",
                log.model,
                log.provider,
                log.prompt_tokens or 0,
                log.completion_tokens or 0,
                log.total_tokens or 0,
                f"{cost_val:.6f}",
                log.latency_ms or 0,
                log.status or "",
                log.guardrail_triggered or ""
            ])
        
        return output.getvalue()

    def get_cost_forecast(
        self,
        db: Session,
        tenant_id: int,
        days_to_forecast: int = 30
    ) -> Dict[str, Any]:
        last_30_days = datetime.utcnow() - timedelta(days=30)
        
        daily_totals = db.query(
            func.coalesce(func.sum(UsageLog.cost), 0.0).label('daily_cost')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= last_30_days
        ).group_by(func.date_trunc('day', UsageLog.created_at)).all()
        
        if daily_totals:
            daily_avg = sum(d.daily_cost for d in daily_totals) / len(daily_totals)
        else:
            daily_avg = 0.0
        
        active_users = db.query(func.count(User.id)).filter(
            User.tenant_id == tenant_id,
            User.status == UserStatus.ACTIVE
        ).scalar() or 0
        
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        monthly_budget = tenant.monthly_budget if tenant else 0
        
        projected_cost = float(daily_avg) * days_to_forecast
        
        return {
            "current_daily_average": float(daily_avg),
            "projected_cost": projected_cost,
            "days_to_forecast": days_to_forecast,
            "active_users": active_users,
            "monthly_budget": monthly_budget,
            "budget_utilization_forecast": (
                projected_cost / monthly_budget * 100
                if monthly_budget > 0 else 0
            ),
            "will_exceed_budget": projected_cost > monthly_budget if monthly_budget > 0 else False
        }


billing_service = BillingService()
