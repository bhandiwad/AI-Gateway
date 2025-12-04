from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import structlog

from backend.app.db.models.department import Department
from backend.app.db.models.team import Team, team_members
from backend.app.db.models.user import User
from backend.app.db.models.api_key import APIKey
from backend.app.db.models.usage_log import UsageLog
from backend.app.schemas.organization import (
    DepartmentCreate, DepartmentUpdate, DepartmentWithStats,
    TeamCreate, TeamUpdate, TeamWithStats,
    OrganizationStats
)

logger = structlog.get_logger()


class OrganizationService:
    """Service for managing organizational structure (departments, teams)."""
    
    # ==================== DEPARTMENT MANAGEMENT ====================
    
    def create_department(
        self,
        db: Session,
        tenant_id: int,
        department_data: DepartmentCreate
    ) -> Department:
        """Create a new department."""
        department = Department(
            tenant_id=tenant_id,
            **department_data.model_dump()
        )
        db.add(department)
        db.commit()
        db.refresh(department)
        
        logger.info(
            "department_created",
            department_id=department.id,
            tenant_id=tenant_id,
            name=department.name
        )
        return department
    
    def get_department(
        self,
        db: Session,
        department_id: int,
        tenant_id: int
    ) -> Optional[Department]:
        """Get department by ID."""
        return db.query(Department).filter(
            Department.id == department_id,
            Department.tenant_id == tenant_id
        ).first()
    
    def list_departments(
        self,
        db: Session,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Department]:
        """List all departments for a tenant."""
        query = db.query(Department).filter(Department.tenant_id == tenant_id)
        
        if is_active is not None:
            query = query.filter(Department.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def update_department(
        self,
        db: Session,
        department_id: int,
        tenant_id: int,
        update_data: DepartmentUpdate
    ) -> Optional[Department]:
        """Update department."""
        department = self.get_department(db, department_id, tenant_id)
        if not department:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(department, key, value)
        
        db.commit()
        db.refresh(department)
        
        logger.info(
            "department_updated",
            department_id=department_id,
            tenant_id=tenant_id
        )
        return department
    
    def delete_department(
        self,
        db: Session,
        department_id: int,
        tenant_id: int
    ) -> bool:
        """Delete department (soft delete by marking inactive)."""
        department = self.get_department(db, department_id, tenant_id)
        if not department:
            return False
        
        department.is_active = False
        db.commit()
        
        logger.info(
            "department_deleted",
            department_id=department_id,
            tenant_id=tenant_id
        )
        return True
    
    def get_department_stats(
        self,
        db: Session,
        department_id: int,
        tenant_id: int
    ) -> Optional[DepartmentWithStats]:
        """Get department with usage statistics."""
        department = self.get_department(db, department_id, tenant_id)
        if not department:
            return None
        
        # Count teams
        team_count = db.query(func.count(Team.id)).filter(
            Team.department_id == department_id
        ).scalar() or 0
        
        # Count users
        user_count = db.query(func.count(User.id)).filter(
            User.department_id == department_id
        ).scalar() or 0
        
        # Count API keys
        api_key_count = db.query(func.count(APIKey.id)).filter(
            APIKey.department_id == department_id
        ).scalar() or 0
        
        # Calculate monthly spend
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_spend = db.query(func.sum(UsageLog.cost)).filter(
            UsageLog.department_id == department_id,
            UsageLog.created_at >= month_start
        ).scalar() or 0.0
        
        # Calculate budget utilization
        budget_utilization = 0.0
        if department.budget_monthly and department.budget_monthly > 0:
            budget_utilization = (monthly_spend / department.budget_monthly) * 100
        
        return DepartmentWithStats(
            **department.__dict__,
            team_count=team_count,
            user_count=user_count,
            api_key_count=api_key_count,
            monthly_spend=monthly_spend,
            budget_utilization=budget_utilization
        )
    
    # ==================== TEAM MANAGEMENT ====================
    
    def create_team(
        self,
        db: Session,
        tenant_id: int,
        team_data: TeamCreate
    ) -> Team:
        """Create a new team."""
        team = Team(
            tenant_id=tenant_id,
            **team_data.model_dump()
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        
        logger.info(
            "team_created",
            team_id=team.id,
            tenant_id=tenant_id,
            name=team.name
        )
        return team
    
    def get_team(
        self,
        db: Session,
        team_id: int,
        tenant_id: int
    ) -> Optional[Team]:
        """Get team by ID."""
        return db.query(Team).filter(
            Team.id == team_id,
            Team.tenant_id == tenant_id
        ).first()
    
    def list_teams(
        self,
        db: Session,
        tenant_id: int,
        department_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Team]:
        """List all teams for a tenant."""
        query = db.query(Team).filter(Team.tenant_id == tenant_id)
        
        if department_id is not None:
            query = query.filter(Team.department_id == department_id)
        
        if is_active is not None:
            query = query.filter(Team.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def update_team(
        self,
        db: Session,
        team_id: int,
        tenant_id: int,
        update_data: TeamUpdate
    ) -> Optional[Team]:
        """Update team."""
        team = self.get_team(db, team_id, tenant_id)
        if not team:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(team, key, value)
        
        db.commit()
        db.refresh(team)
        
        logger.info(
            "team_updated",
            team_id=team_id,
            tenant_id=tenant_id
        )
        return team
    
    def delete_team(
        self,
        db: Session,
        team_id: int,
        tenant_id: int
    ) -> bool:
        """Delete team (soft delete by marking inactive)."""
        team = self.get_team(db, team_id, tenant_id)
        if not team:
            return False
        
        team.is_active = False
        db.commit()
        
        logger.info(
            "team_deleted",
            team_id=team_id,
            tenant_id=tenant_id
        )
        return True
    
    def get_team_stats(
        self,
        db: Session,
        team_id: int,
        tenant_id: int
    ) -> Optional[TeamWithStats]:
        """Get team with usage statistics."""
        team = self.get_team(db, team_id, tenant_id)
        if not team:
            return None
        
        # Count members
        member_count = db.query(func.count(team_members.c.user_id)).filter(
            team_members.c.team_id == team_id
        ).scalar() or 0
        
        # Count API keys
        api_key_count = db.query(func.count(APIKey.id)).filter(
            APIKey.team_id == team_id
        ).scalar() or 0
        
        # Calculate monthly spend
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_spend = db.query(func.sum(UsageLog.cost)).filter(
            UsageLog.team_id == team_id,
            UsageLog.created_at >= month_start
        ).scalar() or 0.0
        
        # Calculate budget utilization
        budget_utilization = 0.0
        if team.budget_monthly and team.budget_monthly > 0:
            budget_utilization = (monthly_spend / team.budget_monthly) * 100
        
        return TeamWithStats(
            **team.__dict__,
            member_count=member_count,
            api_key_count=api_key_count,
            monthly_spend=monthly_spend,
            budget_utilization=budget_utilization
        )
    
    # ==================== TEAM MEMBERS ====================
    
    def add_team_member(
        self,
        db: Session,
        team_id: int,
        user_id: int,
        tenant_id: int,
        role: str = "member"
    ) -> bool:
        """Add user to team."""
        team = self.get_team(db, team_id, tenant_id)
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id
        ).first()
        
        if not team or not user:
            return False
        
        # Check if already a member
        existing = db.query(team_members).filter(
            team_members.c.team_id == team_id,
            team_members.c.user_id == user_id
        ).first()
        
        if existing:
            return False
        
        stmt = team_members.insert().values(
            team_id=team_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.utcnow()
        )
        db.execute(stmt)
        db.commit()
        
        logger.info(
            "team_member_added",
            team_id=team_id,
            user_id=user_id,
            role=role
        )
        return True
    
    def remove_team_member(
        self,
        db: Session,
        team_id: int,
        user_id: int,
        tenant_id: int
    ) -> bool:
        """Remove user from team."""
        team = self.get_team(db, team_id, tenant_id)
        if not team:
            return False
        
        stmt = team_members.delete().where(
            and_(
                team_members.c.team_id == team_id,
                team_members.c.user_id == user_id
            )
        )
        result = db.execute(stmt)
        db.commit()
        
        if result.rowcount > 0:
            logger.info(
                "team_member_removed",
                team_id=team_id,
                user_id=user_id
            )
            return True
        return False
    
    def list_team_members(
        self,
        db: Session,
        team_id: int,
        tenant_id: int
    ) -> List[User]:
        """List all members of a team."""
        team = self.get_team(db, team_id, tenant_id)
        if not team:
            return []
        
        return db.query(User).join(
            team_members,
            User.id == team_members.c.user_id
        ).filter(
            team_members.c.team_id == team_id
        ).all()
    
    # ==================== ANALYTICS ====================
    
    def get_organization_stats(
        self,
        db: Session,
        tenant_id: int
    ) -> OrganizationStats:
        """Get organization-wide statistics."""
        # Count totals
        total_departments = db.query(func.count(Department.id)).filter(
            Department.tenant_id == tenant_id,
            Department.is_active == True
        ).scalar() or 0
        
        total_teams = db.query(func.count(Team.id)).filter(
            Team.tenant_id == tenant_id,
            Team.is_active == True
        ).scalar() or 0
        
        total_users = db.query(func.count(User.id)).filter(
            User.tenant_id == tenant_id
        ).scalar() or 0
        
        total_api_keys = db.query(func.count(APIKey.id)).filter(
            APIKey.tenant_id == tenant_id,
            APIKey.is_active == True
        ).scalar() or 0
        
        # Calculate monthly spend
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total_spend_month = db.query(func.sum(UsageLog.cost)).filter(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= month_start
        ).scalar() or 0.0
        
        # Calculate total budget
        total_budget_month = db.query(func.sum(Department.budget_monthly)).filter(
            Department.tenant_id == tenant_id,
            Department.is_active == True
        ).scalar() or 0.0
        
        # Budget utilization
        budget_utilization = 0.0
        if total_budget_month > 0:
            budget_utilization = (total_spend_month / total_budget_month) * 100
        
        # Top departments by spend
        top_departments = db.query(
            Department.id,
            Department.name,
            func.sum(UsageLog.cost).label('spend')
        ).join(
            UsageLog,
            UsageLog.department_id == Department.id
        ).filter(
            Department.tenant_id == tenant_id,
            UsageLog.created_at >= month_start
        ).group_by(
            Department.id,
            Department.name
        ).order_by(
            func.sum(UsageLog.cost).desc()
        ).limit(5).all()
        
        top_departments_by_spend = [
            {"id": d.id, "name": d.name, "spend": float(d.spend or 0)}
            for d in top_departments
        ]
        
        # Top teams by spend
        top_teams = db.query(
            Team.id,
            Team.name,
            func.sum(UsageLog.cost).label('spend')
        ).join(
            UsageLog,
            UsageLog.team_id == Team.id
        ).filter(
            Team.tenant_id == tenant_id,
            UsageLog.created_at >= month_start
        ).group_by(
            Team.id,
            Team.name
        ).order_by(
            func.sum(UsageLog.cost).desc()
        ).limit(5).all()
        
        top_teams_by_spend = [
            {"id": t.id, "name": t.name, "spend": float(t.spend or 0)}
            for t in top_teams
        ]
        
        return OrganizationStats(
            total_departments=total_departments,
            total_teams=total_teams,
            total_users=total_users,
            total_api_keys=total_api_keys,
            total_spend_month=total_spend_month,
            total_budget_month=total_budget_month,
            budget_utilization=budget_utilization,
            top_departments_by_spend=top_departments_by_spend,
            top_teams_by_spend=top_teams_by_spend
        )


organization_service = OrganizationService()
