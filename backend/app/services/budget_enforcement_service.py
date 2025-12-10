"""
Budget Enforcement Service

Provides granular budget control at multiple levels:
- Model-specific limits
- Route-level limits
- API Key / User limits
- Team limits
- Department limits
- Tenant limits

Budgets are DISABLED by default - must be explicitly enabled.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import structlog

from backend.app.db.models import (
    BudgetPolicy,
    BudgetUsageSnapshot,
    UsageLog,
    Tenant,
    APIKey,
    Team,
    Department
)

logger = structlog.get_logger()


class BudgetCheckResult:
    """Result of a budget check."""
    def __init__(
        self,
        allowed: bool,
        policy: Optional[BudgetPolicy] = None,
        current_usage: float = 0.0,
        limit: float = 0.0,
        percentage_used: float = 0.0,
        warning_level: Optional[str] = None,
        message: str = ""
    ):
        self.allowed = allowed
        self.policy = policy
        self.current_usage = current_usage
        self.limit = limit
        self.percentage_used = percentage_used
        self.warning_level = warning_level
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "policy_id": self.policy.id if self.policy else None,
            "policy_name": self.policy.name if self.policy else None,
            "current_usage_usd": round(self.current_usage, 4),
            "limit_usd": round(self.limit, 2) if self.limit else None,
            "percentage_used": round(self.percentage_used, 1),
            "warning_level": self.warning_level,
            "message": self.message
        }


class BudgetEnforcementService:
    """
    Service for enforcing granular budget policies.
    
    Budget Resolution Order (most specific wins):
    1. Model + Route specific policy
    2. Route-level policy
    3. Model + API Key specific policy
    4. API Key level policy
    5. Model + User specific policy
    6. User level policy
    7. Model + Team specific policy
    8. Team level policy
    9. Model + Department specific policy
    10. Department level policy
    11. Model + Tenant specific policy
    12. Tenant level policy
    13. Global policy (if any)
    """

    def __init__(self, db: Session):
        self.db = db

    def check_budget(
        self,
        tenant_id: int,
        model: str,
        estimated_cost: float = 0.0,
        api_key_id: Optional[int] = None,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        department_id: Optional[int] = None,
        route_id: Optional[int] = None
    ) -> BudgetCheckResult:
        """
        Check if a request is allowed based on budget policies.
        
        Returns BudgetCheckResult with allowed=True if:
        - No enabled budget policies apply
        - All applicable policies are within limits
        """
        
        applicable_policy = self._find_applicable_policy(
            tenant_id=tenant_id,
            model=model,
            api_key_id=api_key_id,
            user_id=user_id,
            team_id=team_id,
            department_id=department_id,
            route_id=route_id
        )
        
        if not applicable_policy:
            return BudgetCheckResult(
                allowed=True,
                message="No budget policy applies"
            )
        
        current_usage = self._get_current_usage(applicable_policy)
        limit = applicable_policy.hard_limit_usd or 0.0
        
        if limit <= 0:
            return BudgetCheckResult(
                allowed=True,
                policy=applicable_policy,
                current_usage=current_usage,
                message="No hard limit set"
            )
        
        projected_usage = current_usage + estimated_cost
        percentage_used = (projected_usage / limit) * 100 if limit > 0 else 0
        
        warning_level = self._get_warning_level(applicable_policy, percentage_used)
        
        if percentage_used >= 100:
            action = applicable_policy.action_on_limit or "block"
            
            if action == "block":
                return BudgetCheckResult(
                    allowed=False,
                    policy=applicable_policy,
                    current_usage=current_usage,
                    limit=limit,
                    percentage_used=percentage_used,
                    warning_level="exceeded",
                    message=f"Budget limit exceeded: ${current_usage:.2f} / ${limit:.2f} ({percentage_used:.1f}%)"
                )
            elif action == "warn":
                logger.warning(
                    "budget_limit_exceeded_warning",
                    policy_id=applicable_policy.id,
                    current_usage=current_usage,
                    limit=limit
                )
        
        return BudgetCheckResult(
            allowed=True,
            policy=applicable_policy,
            current_usage=current_usage,
            limit=limit,
            percentage_used=percentage_used,
            warning_level=warning_level,
            message=f"Budget OK: ${current_usage:.2f} / ${limit:.2f} ({percentage_used:.1f}%)"
        )

    def _find_applicable_policy(
        self,
        tenant_id: int,
        model: str,
        api_key_id: Optional[int] = None,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        department_id: Optional[int] = None,
        route_id: Optional[int] = None
    ) -> Optional[BudgetPolicy]:
        """Find the most specific applicable enabled budget policy."""
        
        search_order = []
        
        if route_id:
            search_order.append(("route", route_id, model))
            search_order.append(("route", route_id, None))
        
        if api_key_id:
            search_order.append(("api_key", api_key_id, model))
            search_order.append(("api_key", api_key_id, None))
        
        if user_id:
            search_order.append(("user", user_id, model))
            search_order.append(("user", user_id, None))
        
        if team_id:
            search_order.append(("team", team_id, model))
            search_order.append(("team", team_id, None))
        
        if department_id:
            search_order.append(("department", department_id, model))
            search_order.append(("department", department_id, None))
        
        search_order.append(("tenant", tenant_id, model))
        search_order.append(("tenant", tenant_id, None))
        
        search_order.append(("global", None, model))
        search_order.append(("global", None, None))
        
        for scope_type, scope_id, model_filter in search_order:
            query = self.db.query(BudgetPolicy).filter(
                BudgetPolicy.enabled == True,
                BudgetPolicy.scope_type == scope_type
            )
            
            if scope_id is not None:
                query = query.filter(BudgetPolicy.scope_id == scope_id)
            
            if model_filter:
                query = query.filter(
                    or_(
                        BudgetPolicy.model_filter == model_filter,
                        BudgetPolicy.model_filter.like(f"%{model_filter.split('/')[0]}%")
                    )
                )
            else:
                query = query.filter(
                    or_(
                        BudgetPolicy.model_filter == None,
                        BudgetPolicy.model_filter == ""
                    )
                )
            
            if scope_type != "global":
                query = query.filter(BudgetPolicy.tenant_id == tenant_id)
            
            policy = query.first()
            if policy:
                return policy
        
        return None

    def _get_current_usage(self, policy: BudgetPolicy) -> float:
        """Get current usage for a budget policy period."""
        
        period_start, period_end = self._get_period_bounds(policy.period)
        
        snapshot = self.db.query(BudgetUsageSnapshot).filter(
            BudgetUsageSnapshot.policy_id == policy.id,
            BudgetUsageSnapshot.period_start == period_start
        ).first()
        
        if snapshot:
            return snapshot.total_cost_usd
        
        return self._calculate_usage_from_logs(policy, period_start, period_end)

    def _calculate_usage_from_logs(
        self,
        policy: BudgetPolicy,
        period_start: datetime,
        period_end: datetime
    ) -> float:
        """Calculate usage directly from usage logs."""
        
        query = self.db.query(func.coalesce(func.sum(UsageLog.cost), 0.0))
        
        query = query.filter(
            UsageLog.created_at >= period_start,
            UsageLog.created_at < period_end
        )
        
        if policy.scope_type == "tenant":
            query = query.filter(UsageLog.tenant_id == policy.scope_id)
        elif policy.scope_type == "department":
            query = query.filter(UsageLog.department_id == policy.scope_id)
        elif policy.scope_type == "team":
            query = query.filter(UsageLog.team_id == policy.scope_id)
        elif policy.scope_type == "api_key":
            query = query.filter(UsageLog.api_key_id == policy.scope_id)
        elif policy.scope_type == "user":
            query = query.filter(UsageLog.user_id == policy.scope_id)
        elif policy.scope_type == "route":
            query = query.filter(UsageLog.endpoint.like(f"%route_{policy.scope_id}%"))
        
        if policy.model_filter:
            query = query.filter(UsageLog.model == policy.model_filter)
        
        return query.scalar() or 0.0

    def _get_period_bounds(self, period: str) -> Tuple[datetime, datetime]:
        """Get the start and end of the current budget period."""
        now = datetime.utcnow()
        
        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == "weekly":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        elif period == "monthly":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start.replace(day=28) + timedelta(days=4)
            end = next_month.replace(day=1)
        elif period == "quarterly":
            quarter = (now.month - 1) // 3
            start = now.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=92)
            end = end.replace(day=1)
        elif period == "yearly":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
        else:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start.replace(day=28) + timedelta(days=4)
            end = next_month.replace(day=1)
        
        return start, end

    def _get_warning_level(self, policy: BudgetPolicy, percentage_used: float) -> Optional[str]:
        """Determine warning level based on thresholds."""
        
        if percentage_used >= 100:
            return "exceeded"
        elif percentage_used >= (policy.critical_threshold_pct or 95):
            return "critical"
        elif percentage_used >= (policy.warning_threshold_pct or 90):
            return "warning"
        elif percentage_used >= (policy.soft_threshold_pct or 80):
            return "soft"
        
        return None

    def get_budget_summary(
        self,
        tenant_id: int,
        scope_type: Optional[str] = None,
        scope_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get summary of all budget policies for a tenant."""
        
        query = self.db.query(BudgetPolicy).filter(
            BudgetPolicy.tenant_id == tenant_id
        )
        
        if scope_type:
            query = query.filter(BudgetPolicy.scope_type == scope_type)
        if scope_id:
            query = query.filter(BudgetPolicy.scope_id == scope_id)
        
        policies = query.all()
        
        summaries = []
        for policy in policies:
            current_usage = self._get_current_usage(policy)
            limit = policy.hard_limit_usd or 0.0
            percentage_used = (current_usage / limit * 100) if limit > 0 else 0
            
            summaries.append({
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "enabled": policy.enabled,
                "scope_type": policy.scope_type,
                "scope_id": policy.scope_id,
                "model_filter": policy.model_filter,
                "period": policy.period,
                "hard_limit_usd": limit,
                "current_usage_usd": round(current_usage, 4),
                "percentage_used": round(percentage_used, 1),
                "warning_level": self._get_warning_level(policy, percentage_used),
                "action_on_limit": policy.action_on_limit,
                "soft_threshold_pct": policy.soft_threshold_pct,
                "warning_threshold_pct": policy.warning_threshold_pct,
                "critical_threshold_pct": policy.critical_threshold_pct,
                "created_at": policy.created_at.isoformat() if policy.created_at else None
            })
        
        return summaries

    def create_policy(
        self,
        tenant_id: int,
        name: str,
        scope_type: str,
        scope_id: Optional[int] = None,
        model_filter: Optional[str] = None,
        period: str = "monthly",
        hard_limit_usd: Optional[float] = None,
        action_on_limit: str = "block",
        enabled: bool = False,
        created_by_user_id: Optional[int] = None,
        **kwargs
    ) -> BudgetPolicy:
        """Create a new budget policy (disabled by default)."""
        
        policy = BudgetPolicy(
            tenant_id=tenant_id,
            name=name,
            scope_type=scope_type,
            scope_id=scope_id,
            model_filter=model_filter,
            period=period,
            hard_limit_usd=hard_limit_usd,
            action_on_limit=action_on_limit,
            enabled=enabled,
            created_by_user_id=created_by_user_id,
            soft_threshold_pct=kwargs.get("soft_threshold_pct", 80.0),
            warning_threshold_pct=kwargs.get("warning_threshold_pct", 90.0),
            critical_threshold_pct=kwargs.get("critical_threshold_pct", 95.0),
            alert_recipients=kwargs.get("alert_recipients", []),
            description=kwargs.get("description")
        )
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        logger.info(
            "budget_policy_created",
            policy_id=policy.id,
            name=name,
            scope_type=scope_type,
            enabled=enabled
        )
        
        return policy

    def update_policy(
        self,
        policy_id: int,
        tenant_id: int,
        **updates
    ) -> Optional[BudgetPolicy]:
        """Update an existing budget policy."""
        
        policy = self.db.query(BudgetPolicy).filter(
            BudgetPolicy.id == policy_id,
            BudgetPolicy.tenant_id == tenant_id
        ).first()
        
        if not policy:
            return None
        
        allowed_fields = [
            "name", "description", "enabled", "model_filter", "period",
            "hard_limit_usd", "action_on_limit", "soft_threshold_pct",
            "warning_threshold_pct", "critical_threshold_pct", "alert_recipients"
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(policy, field, value)
        
        self.db.commit()
        self.db.refresh(policy)
        
        logger.info(
            "budget_policy_updated",
            policy_id=policy_id,
            updates=list(updates.keys())
        )
        
        return policy

    def delete_policy(self, policy_id: int, tenant_id: int) -> bool:
        """Delete a budget policy."""
        
        policy = self.db.query(BudgetPolicy).filter(
            BudgetPolicy.id == policy_id,
            BudgetPolicy.tenant_id == tenant_id
        ).first()
        
        if not policy:
            return False
        
        self.db.delete(policy)
        self.db.commit()
        
        logger.info("budget_policy_deleted", policy_id=policy_id)
        return True


def get_budget_service(db: Session) -> BudgetEnforcementService:
    """Get a budget enforcement service instance."""
    return BudgetEnforcementService(db)
