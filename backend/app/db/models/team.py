from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.db.session import Base


team_members = Table(
    'team_members',
    Base.metadata,
    Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role', String(50), default='member'),
    Column('joined_at', DateTime, default=datetime.utcnow)
)


class Team(Base):
    """Team for organizational structure (within departments)."""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    budget_monthly = Column(Float, nullable=True)
    current_spend = Column(Float, default=0.0)
    
    lead_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    tags = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    department = relationship("Department", back_populates="teams")
    lead = relationship("User", foreign_keys=[lead_user_id])
    members = relationship("User", secondary=team_members, back_populates="teams")
    api_keys = relationship("APIKey", back_populates="team")
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
