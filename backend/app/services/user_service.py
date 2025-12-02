from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import bcrypt

from backend.app.db.models.user import User, UserRole, UserStatus
from backend.app.db.models.usage_log import UsageLog


class UserService:
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def create_user(
        self,
        db: Session,
        tenant_id: int,
        email: str,
        name: str,
        password: Optional[str] = None,
        role: UserRole = UserRole.USER,
        status: UserStatus = UserStatus.ACTIVE,
        sso_provider: Optional[str] = None,
        sso_user_id: Optional[str] = None,
        allowed_models: Optional[List[str]] = None,
        rate_limit: int = 60,
        monthly_budget: int = 100
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            email=email,
            name=name,
            password_hash=self.hash_password(password) if password else None,
            role=role,
            status=status,
            sso_provider=sso_provider,
            sso_user_id=sso_user_id,
            allowed_models=allowed_models or [],
            rate_limit=rate_limit,
            monthly_budget=monthly_budget
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, db: Session, tenant_id: int, email: str) -> Optional[User]:
        return db.query(User).filter(
            User.tenant_id == tenant_id,
            User.email == email
        ).first()

    def get_user_by_sso(self, db: Session, tenant_id: int, sso_provider: str, sso_user_id: str) -> Optional[User]:
        return db.query(User).filter(
            User.tenant_id == tenant_id,
            User.sso_provider == sso_provider,
            User.sso_user_id == sso_user_id
        ).first()

    def get_users_by_tenant(
        self,
        db: Session,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[UserStatus] = None
    ) -> List[User]:
        query = db.query(User).filter(User.tenant_id == tenant_id)
        if status:
            query = query.filter(User.status == status)
        return query.offset(skip).limit(limit).all()

    def count_users_by_tenant(self, db: Session, tenant_id: int, status: Optional[UserStatus] = None) -> int:
        query = db.query(func.count(User.id)).filter(User.tenant_id == tenant_id)
        if status:
            query = query.filter(User.status == status)
        return query.scalar() or 0

    def update_user(self, db: Session, user_id: int, updates: Dict[str, Any]) -> Optional[User]:
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        for key, value in updates.items():
            if hasattr(user, key) and value is not None:
                if key == "password":
                    user.password_hash = self.hash_password(value)
                else:
                    setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user

    def update_user_spend(self, db: Session, user_id: int, cost: float) -> None:
        user = self.get_user_by_id(db, user_id)
        if user:
            user.current_spend = (user.current_spend or 0) + cost
            db.commit()

    def reset_monthly_spend(self, db: Session, tenant_id: int) -> int:
        result = db.query(User).filter(User.tenant_id == tenant_id).update(
            {"current_spend": 0}
        )
        db.commit()
        return result

    def delete_user(self, db: Session, user_id: int) -> bool:
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True

    def get_user_usage_summary(
        self,
        db: Session,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(
            func.count(UsageLog.id).label('total_requests'),
            func.sum(UsageLog.total_tokens).label('total_tokens'),
            func.sum(UsageLog.cost).label('total_cost'),
            func.avg(UsageLog.latency_ms).label('avg_latency')
        ).filter(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= start_date
        ).first()
        
        by_model = db.query(
            UsageLog.model,
            func.count(UsageLog.id).label('requests'),
            func.sum(UsageLog.cost).label('cost')
        ).filter(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= start_date
        ).group_by(UsageLog.model).all()
        
        return {
            "total_requests": stats.total_requests or 0,
            "total_tokens": int(stats.total_tokens or 0),
            "total_cost": float(stats.total_cost or 0),
            "avg_latency_ms": float(stats.avg_latency or 0),
            "by_model": {
                m.model: {"requests": m.requests, "cost": float(m.cost or 0)}
                for m in by_model
            }
        }

    def authenticate_user(
        self,
        db: Session,
        tenant_id: int,
        email: str,
        password: str
    ) -> Optional[User]:
        user = self.get_user_by_email(db, tenant_id, email)
        if not user:
            return None
        
        if user.sso_provider and not user.password_hash:
            return None
        
        if not user.password_hash:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        if user.status != UserStatus.ACTIVE:
            return None
        
        user.last_login_at = datetime.utcnow()
        db.commit()
        return user

    def authenticate_sso_user(
        self,
        db: Session,
        tenant_id: int,
        sso_provider: str,
        sso_user_id: str,
        email: str,
        name: str
    ) -> User:
        user = self.get_user_by_sso(db, tenant_id, sso_provider, sso_user_id)
        if not user:
            user = self.get_user_by_email(db, tenant_id, email)
            if user:
                user.sso_provider = sso_provider
                user.sso_user_id = sso_user_id
            else:
                user = User(
                    tenant_id=tenant_id,
                    email=email,
                    name=name,
                    sso_provider=sso_provider,
                    sso_user_id=sso_user_id,
                    status=UserStatus.ACTIVE,
                    role=UserRole.USER
                )
                db.add(user)
        
        if user.status == UserStatus.PENDING:
            user.status = UserStatus.ACTIVE
        
        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user


user_service = UserService()
