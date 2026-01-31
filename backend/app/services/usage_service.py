from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
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

    def get_usage_by_api_key(
        self,
        db: Session,
        tenant_id: int,
        days: int = 30,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        from backend.app.db.models.api_key import APIKey
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(
            UsageLog.api_key_id,
            APIKey.name.label('key_name'),
            func.count(UsageLog.id).label('requests'),
            func.sum(UsageLog.total_tokens).label('tokens'),
            func.sum(UsageLog.cost).label('cost'),
            func.avg(UsageLog.latency_ms).label('avg_latency'),
            func.count(case((UsageLog.status == 'success', 1))).label('success_count')
        ).join(
            APIKey, UsageLog.api_key_id == APIKey.id, isouter=True
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).group_by(UsageLog.api_key_id, APIKey.name).order_by(
            desc(func.count(UsageLog.id))
        ).limit(limit).all()
        
        return [
            {
                "api_key_id": s.api_key_id,
                "key_name": s.key_name or f"Key #{s.api_key_id}",
                "requests": s.requests,
                "tokens": int(s.tokens or 0),
                "cost": float(s.cost or 0),
                "avg_latency_ms": float(s.avg_latency or 0),
                "success_rate": round((s.success_count / s.requests * 100) if s.requests > 0 else 0, 1)
            }
            for s in stats
        ]

    def get_usage_by_user(
        self,
        db: Session,
        tenant_id: int,
        days: int = 30,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        from backend.app.db.models.api_key import APIKey
        from backend.app.db.models.user import User
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(
            APIKey.user_id,
            User.name.label('user_name'),
            User.email.label('user_email'),
            func.count(UsageLog.id).label('requests'),
            func.sum(UsageLog.total_tokens).label('tokens'),
            func.sum(UsageLog.cost).label('cost'),
            func.avg(UsageLog.latency_ms).label('avg_latency')
        ).join(
            APIKey, UsageLog.api_key_id == APIKey.id
        ).join(
            User, APIKey.user_id == User.id, isouter=True
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).group_by(APIKey.user_id, User.name, User.email).order_by(
            desc(func.count(UsageLog.id))
        ).limit(limit).all()
        
        return [
            {
                "user_id": s.user_id,
                "user_name": s.user_name or "Unknown",
                "user_email": s.user_email or "",
                "requests": s.requests,
                "tokens": int(s.tokens or 0),
                "cost": float(s.cost or 0),
                "avg_latency_ms": float(s.avg_latency or 0)
            }
            for s in stats
        ]

    def get_usage_by_department(
        self,
        db: Session,
        tenant_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        from backend.app.db.models.api_key import APIKey
        from backend.app.db.models.user import User
        from backend.app.db.models.organization import Department
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(
            User.department_id,
            Department.name.label('department_name'),
            func.count(UsageLog.id).label('requests'),
            func.sum(UsageLog.total_tokens).label('tokens'),
            func.sum(UsageLog.cost).label('cost')
        ).join(
            APIKey, UsageLog.api_key_id == APIKey.id
        ).join(
            User, APIKey.user_id == User.id
        ).join(
            Department, User.department_id == Department.id, isouter=True
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).group_by(User.department_id, Department.name).order_by(
            desc(func.sum(UsageLog.cost))
        ).all()
        
        return [
            {
                "department_id": s.department_id,
                "department_name": s.department_name or "Unassigned",
                "requests": s.requests,
                "tokens": int(s.tokens or 0),
                "cost": float(s.cost or 0)
            }
            for s in stats
        ]

    def get_hourly_distribution(
        self,
        db: Session,
        tenant_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(
            func.extract('hour', UsageLog.created_at).label('hour'),
            func.count(UsageLog.id).label('requests'),
            func.avg(UsageLog.latency_ms).label('avg_latency')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).group_by(
            func.extract('hour', UsageLog.created_at)
        ).order_by('hour').all()
        
        return [
            {
                "hour": int(s.hour),
                "requests": s.requests,
                "avg_latency_ms": float(s.avg_latency or 0)
            }
            for s in stats
        ]

    def get_error_breakdown(
        self,
        db: Session,
        tenant_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total = db.query(func.count(UsageLog.id)).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).scalar() or 0
        
        by_status = db.query(
            UsageLog.status,
            func.count(UsageLog.id).label('count')
        ).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start_date
        ).group_by(UsageLog.status).all()
        
        status_breakdown = {s.status: s.count for s in by_status}
        
        return {
            "total_requests": total,
            "success": status_breakdown.get('success', 0),
            "errors": total - status_breakdown.get('success', 0),
            "cache_hits": status_breakdown.get('cache_hit', 0),
            "by_status": status_breakdown
        }

    def get_detailed_stats(
        self,
        db: Session,
        tenant_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive statistics for the stats page."""
        return {
            "summary": self.get_usage_summary(db, tenant_id, days),
            "top_models": self.get_top_models(db, tenant_id, days, limit=10),
            "by_api_key": self.get_usage_by_api_key(db, tenant_id, days, limit=10),
            "by_user": self.get_usage_by_user(db, tenant_id, days, limit=10),
            "by_department": self.get_usage_by_department(db, tenant_id, days),
            "hourly_distribution": self.get_hourly_distribution(db, tenant_id, min(days, 7)),
            "error_breakdown": self.get_error_breakdown(db, tenant_id, days),
            "usage_over_time": self.get_usage_over_time(db, tenant_id, days)
        }


usage_service = UsageService()
