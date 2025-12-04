"""
Quota and Cost Limit Checker Middleware

Checks API key and tenant cost limits before processing requests.
Prevents requests if daily/monthly limits are exceeded.
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import logging

from backend.app.db.models import APIKey, Tenant, UsageLog, User

logger = logging.getLogger(__name__)


class QuotaChecker:
    """Check and enforce quota limits for API keys, users, and tenants"""
    
    def check_api_key_limits(
        self,
        db: Session,
        api_key: APIKey,
        estimated_cost: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if API key has exceeded cost limits.
        
        Args:
            db: Database session
            api_key: The API key object
            estimated_cost: Estimated cost of the upcoming request
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if not api_key.cost_limit_daily and not api_key.cost_limit_monthly:
            return True, None  # No limits set
        
        now = datetime.utcnow()
        
        # Check daily limit
        if api_key.cost_limit_daily:
            day_start = datetime(now.year, now.month, now.day)
            daily_spend = db.query(func.sum(UsageLog.cost)).filter(
                UsageLog.api_key_id == api_key.id,
                UsageLog.created_at >= day_start,
                UsageLog.status.in_(["success", "cache_hit"])
            ).scalar() or 0.0
            
            if daily_spend + estimated_cost > api_key.cost_limit_daily:
                logger.warning(
                    f"API key {api_key.id} exceeded daily cost limit: "
                    f"${daily_spend:.4f} / ${api_key.cost_limit_daily:.4f}"
                )
                return False, (
                    f"Daily cost limit exceeded for this API key. "
                    f"Limit: ${api_key.cost_limit_daily:.2f}, "
                    f"Current spend: ${daily_spend:.2f}. "
                    f"Limit resets at midnight UTC."
                )
        
        # Check monthly limit
        if api_key.cost_limit_monthly:
            month_start = datetime(now.year, now.month, 1)
            monthly_spend = db.query(func.sum(UsageLog.cost)).filter(
                UsageLog.api_key_id == api_key.id,
                UsageLog.created_at >= month_start,
                UsageLog.status.in_(["success", "cache_hit"])
            ).scalar() or 0.0
            
            if monthly_spend + estimated_cost > api_key.cost_limit_monthly:
                logger.warning(
                    f"API key {api_key.id} exceeded monthly cost limit: "
                    f"${monthly_spend:.4f} / ${api_key.cost_limit_monthly:.4f}"
                )
                return False, (
                    f"Monthly cost limit exceeded for this API key. "
                    f"Limit: ${api_key.cost_limit_monthly:.2f}, "
                    f"Current spend: ${monthly_spend:.2f}. "
                    f"Limit resets on the 1st of next month."
                )
        
        return True, None
    
    def check_user_limits(
        self,
        db: Session,
        user_id: int,
        estimated_cost: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded their budget.
        
        Args:
            db: Database session
            user_id: User ID
            estimated_cost: Estimated cost of the upcoming request
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.monthly_budget:
            return True, None  # No budget set
        
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        monthly_spend = db.query(func.sum(UsageLog.cost)).filter(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= month_start,
            UsageLog.status.in_(["success", "cache_hit"])
        ).scalar() or 0.0
        
        if monthly_spend + estimated_cost > user.monthly_budget:
            logger.warning(
                f"User {user_id} exceeded monthly budget: "
                f"${monthly_spend:.4f} / ${user.monthly_budget:.4f}"
            )
            return False, (
                f"Your monthly budget has been exceeded. "
                f"Budget: ${user.monthly_budget:.2f}, "
                f"Current spend: ${monthly_spend:.2f}. "
                f"Please contact your administrator to increase your budget."
            )
        
        # Warning if approaching limit (90%)
        if monthly_spend + estimated_cost > user.monthly_budget * 0.9:
            logger.info(
                f"User {user_id} approaching monthly budget limit: "
                f"${monthly_spend:.4f} / ${user.monthly_budget:.4f}"
            )
        
        return True, None
    
    def check_tenant_limits(
        self,
        db: Session,
        tenant_id: int,
        estimated_cost: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if tenant has exceeded their budget.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            estimated_cost: Estimated cost of the upcoming request
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant or not tenant.monthly_budget:
            return True, None  # No budget set
        
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        monthly_spend = db.query(func.sum(UsageLog.cost)).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= month_start,
            UsageLog.status.in_(["success", "cache_hit"])
        ).scalar() or 0.0
        
        if monthly_spend + estimated_cost > tenant.monthly_budget:
            logger.warning(
                f"Tenant {tenant_id} exceeded monthly budget: "
                f"${monthly_spend:.4f} / ${tenant.monthly_budget:.4f}"
            )
            return False, (
                f"Organization monthly budget has been exceeded. "
                f"Budget: ${tenant.monthly_budget:.2f}, "
                f"Current spend: ${monthly_spend:.2f}. "
                f"Please contact support to increase your organization's budget."
            )
        
        # Warning if approaching limit (90%)
        if monthly_spend + estimated_cost > tenant.monthly_budget * 0.9:
            logger.info(
                f"Tenant {tenant_id} approaching monthly budget limit: "
                f"${monthly_spend:.4f} / ${tenant.monthly_budget:.4f}"
            )
        
        return True, None
    
    def check_department_limits(
        self,
        db: Session,
        department_id: int,
        estimated_cost: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if department has exceeded its budget.
        
        Args:
            db: Database session
            department_id: Department ID
            estimated_cost: Estimated cost of the upcoming request
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        from backend.app.db.models import Department
        
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department or not department.budget_monthly:
            return True, None  # No budget set
        
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        monthly_spend = db.query(func.sum(UsageLog.cost)).filter(
            UsageLog.department_id == department_id,
            UsageLog.created_at >= month_start,
            UsageLog.status.in_(["success", "cache_hit"])
        ).scalar() or 0.0
        
        if monthly_spend + estimated_cost > department.budget_monthly:
            logger.warning(
                f"Department {department_id} exceeded monthly budget: "
                f"${monthly_spend:.4f} / ${department.budget_monthly:.4f}"
            )
            return False, (
                f"Department monthly budget has been exceeded. "
                f"Budget: ${department.budget_monthly:.2f}, "
                f"Current spend: ${monthly_spend:.2f}. "
                f"Please contact your department manager to increase the budget."
            )
        
        return True, None
    
    def check_team_limits(
        self,
        db: Session,
        team_id: int,
        estimated_cost: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if team has exceeded its budget.
        
        Args:
            db: Database session
            team_id: Team ID
            estimated_cost: Estimated cost of the upcoming request
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        from backend.app.db.models import Team
        
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team or not team.budget_monthly:
            return True, None  # No budget set
        
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        monthly_spend = db.query(func.sum(UsageLog.cost)).filter(
            UsageLog.team_id == team_id,
            UsageLog.created_at >= month_start,
            UsageLog.status.in_(["success", "cache_hit"])
        ).scalar() or 0.0
        
        if monthly_spend + estimated_cost > team.budget_monthly:
            logger.warning(
                f"Team {team_id} exceeded monthly budget: "
                f"${monthly_spend:.4f} / ${team.budget_monthly:.4f}"
            )
            return False, (
                f"Team monthly budget has been exceeded. "
                f"Budget: ${team.budget_monthly:.2f}, "
                f"Current spend: ${monthly_spend:.2f}. "
                f"Please contact your team lead to increase the budget."
            )
        
        return True, None
    
    def check_all_limits(
        self,
        db: Session,
        api_key: APIKey,
        tenant: Tenant,
        user_id: Optional[int] = None,
        estimated_cost: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Check all applicable limits in order of specificity:
        API Key -> User -> Team -> Department -> Tenant
        
        Returns on first violation found.
        
        Args:
            db: Database session
            api_key: API key object
            tenant: Tenant object
            user_id: Optional user ID
            estimated_cost: Estimated cost
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Check API key limits (most specific)
        is_allowed, error_msg = self.check_api_key_limits(db, api_key, estimated_cost)
        if not is_allowed:
            return False, error_msg
        
        # Check team limits if API key belongs to a team
        if api_key.team_id:
            is_allowed, error_msg = self.check_team_limits(db, api_key.team_id, estimated_cost)
            if not is_allowed:
                return False, error_msg
        
        # Check department limits if API key belongs to a department
        if api_key.department_id:
            is_allowed, error_msg = self.check_department_limits(db, api_key.department_id, estimated_cost)
            if not is_allowed:
                return False, error_msg
        
        # Check user limits if provided
        if user_id:
            is_allowed, error_msg = self.check_user_limits(db, user_id, estimated_cost)
            if not is_allowed:
                return False, error_msg
        
        # Check tenant limits (least specific, organization-wide)
        is_allowed, error_msg = self.check_tenant_limits(db, tenant.id, estimated_cost)
        if not is_allowed:
            return False, error_msg
        
        return True, None
    
    def get_remaining_budget(
        self,
        db: Session,
        api_key: APIKey,
        tenant: Tenant
    ) -> Dict[str, float]:
        """
        Get remaining budget information for all applicable limits.
        
        Returns:
            Dict with remaining budgets for each level
        """
        now = datetime.utcnow()
        day_start = datetime(now.year, now.month, now.day)
        month_start = datetime(now.year, now.month, 1)
        
        result = {}
        
        # API key limits
        if api_key.cost_limit_daily:
            daily_spend = db.query(func.sum(UsageLog.cost)).filter(
                UsageLog.api_key_id == api_key.id,
                UsageLog.created_at >= day_start,
                UsageLog.status.in_(["success", "cache_hit"])
            ).scalar() or 0.0
            result["api_key_daily_remaining"] = max(0, api_key.cost_limit_daily - daily_spend)
        
        if api_key.cost_limit_monthly:
            monthly_spend = db.query(func.sum(UsageLog.cost)).filter(
                UsageLog.api_key_id == api_key.id,
                UsageLog.created_at >= month_start,
                UsageLog.status.in_(["success", "cache_hit"])
            ).scalar() or 0.0
            result["api_key_monthly_remaining"] = max(0, api_key.cost_limit_monthly - monthly_spend)
        
        # Tenant limits
        if tenant.monthly_budget:
            monthly_spend = db.query(func.sum(UsageLog.cost)).filter(
                UsageLog.tenant_id == tenant.id,
                UsageLog.created_at >= month_start,
                UsageLog.status.in_(["success", "cache_hit"])
            ).scalar() or 0.0
            result["tenant_monthly_remaining"] = max(0, tenant.monthly_budget - monthly_spend)
        
        return result


# Global quota checker instance
quota_checker = QuotaChecker()
