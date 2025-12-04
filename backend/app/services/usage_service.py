from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from backend.app.db.models import UsageLog, Tenant, APIKey


class UsageService:
    def log_usage(
        self,
        db: Session,
        tenant_id: int,
        api_key_id: Optional[int],
        request_id: str,
        endpoint: str,
        model: str,
        provider: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
        latency_ms: int = 0,
        status: str = "success",
        error_message: Optional[str] = None,
        guardrail_triggered: Optional[str] = None,
        guardrail_action: Optional[str] = None,
        request_metadata: Optional[Dict] = None,
        response_metadata: Optional[Dict] = None,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None
    ) -> UsageLog:
        # If department/team not provided, try to derive from API key
        if api_key_id and (department_id is None or team_id is None):
            api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
            if api_key:
                if department_id is None:
                    department_id = api_key.department_id
                if team_id is None:
                    team_id = api_key.team_id
                if user_id is None:
                    user_id = api_key.owner_user_id
        
        usage_log = UsageLog(
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            user_id=user_id,
            department_id=department_id,
            team_id=team_id,
            request_id=request_id,
            endpoint=endpoint,
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
            guardrail_triggered=guardrail_triggered,
            guardrail_action=guardrail_action,
            request_metadata=request_metadata or {},
            response_metadata=response_metadata or {}
        )
        
        db.add(usage_log)
        db.commit()
        db.refresh(usage_log)
        
        return usage_log
    
    def get_usage_logs(
        self,
        db: Session,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model: Optional[str] = None
    ) -> List[UsageLog]:
        query = db.query(UsageLog).filter(UsageLog.tenant_id == tenant_id)
        
        if start_date:
            query = query.filter(UsageLog.created_at >= start_date)
        if end_date:
            query = query.filter(UsageLog.created_at <= end_date)
        if model:
            query = query.filter(UsageLog.model == model)
        
        return query.order_by(desc(UsageLog.created_at)).offset(skip).limit(limit).all()
    
    def get_usage_summary(
        self,
        db: Session,
        tenant_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        base_query = db.query(UsageLog).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        )
        
        total_stats = db.query(
            func.count(UsageLog.id).label('total_requests'),
            func.sum(UsageLog.total_tokens).label('total_tokens'),
            func.sum(UsageLog.cost).label('total_cost'),
            func.avg(UsageLog.latency_ms).label('avg_latency')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).first()
        
        success_count = base_query.filter(UsageLog.status == "success").count()
        total_count = total_stats.total_requests or 0
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        by_model = {}
        model_stats = db.query(
            UsageLog.model,
            func.count(UsageLog.id).label('requests'),
            func.sum(UsageLog.total_tokens).label('tokens'),
            func.sum(UsageLog.cost).label('cost')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).group_by(UsageLog.model).all()
        
        for stat in model_stats:
            by_model[stat.model] = {
                "requests": stat.requests,
                "tokens": stat.tokens or 0,
                "cost": float(stat.cost or 0)
            }
        
        by_provider = {}
        provider_stats = db.query(
            UsageLog.provider,
            func.count(UsageLog.id).label('requests'),
            func.sum(UsageLog.total_tokens).label('tokens'),
            func.sum(UsageLog.cost).label('cost')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).group_by(UsageLog.provider).all()
        
        for stat in provider_stats:
            by_provider[stat.provider] = {
                "requests": stat.requests,
                "tokens": stat.tokens or 0,
                "cost": float(stat.cost or 0)
            }
        
        return {
            "total_requests": total_count,
            "total_tokens": int(total_stats.total_tokens or 0),
            "total_cost": float(total_stats.total_cost or 0),
            "avg_latency_ms": float(total_stats.avg_latency or 0),
            "success_rate": success_rate,
            "by_model": by_model,
            "by_provider": by_provider
        }
    
    def get_usage_over_time(
        self,
        db: Session,
        tenant_id: int,
        days: int = 30,
        interval: str = "day"
    ) -> List[Dict[str, Any]]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        if interval == "hour":
            date_trunc = func.date_trunc('hour', UsageLog.created_at)
        else:
            date_trunc = func.date_trunc('day', UsageLog.created_at)
        
        time_series = db.query(
            date_trunc.label('timestamp'),
            func.count(UsageLog.id).label('requests'),
            func.sum(UsageLog.total_tokens).label('tokens'),
            func.sum(UsageLog.cost).label('cost')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).group_by(date_trunc).order_by(date_trunc).all()
        
        return [
            {
                "timestamp": ts.timestamp.isoformat() if ts.timestamp else None,
                "requests": ts.requests,
                "tokens": int(ts.tokens or 0),
                "cost": float(ts.cost or 0)
            }
            for ts in time_series
        ]
    
    def get_top_models(
        self,
        db: Session,
        tenant_id: int,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        top_models = db.query(
            UsageLog.model,
            UsageLog.provider,
            func.count(UsageLog.id).label('requests'),
            func.sum(UsageLog.total_tokens).label('tokens'),
            func.sum(UsageLog.cost).label('cost'),
            func.avg(UsageLog.latency_ms).label('avg_latency')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).group_by(UsageLog.model, UsageLog.provider).order_by(
            desc(func.count(UsageLog.id))
        ).limit(limit).all()
        
        return [
            {
                "model": m.model,
                "provider": m.provider,
                "requests": m.requests,
                "tokens": int(m.tokens or 0),
                "cost": float(m.cost or 0),
                "avg_latency_ms": float(m.avg_latency or 0)
            }
            for m in top_models
        ]


usage_service = UsageService()
