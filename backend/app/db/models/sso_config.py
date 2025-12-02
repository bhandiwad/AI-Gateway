from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.app.db.session import Base


class SSOProtocol(str, enum.Enum):
    OIDC = "oidc"
    SAML = "saml"


class SSOConfig(Base):
    __tablename__ = "sso_configs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True)
    
    enabled = Column(Boolean, default=False)
    protocol = Column(SQLEnum(SSOProtocol), default=SSOProtocol.OIDC)
    
    provider_name = Column(String(100))
    
    client_id = Column(String(255))
    client_secret = Column(Text)
    
    issuer_url = Column(String(500))
    authorization_endpoint = Column(String(500))
    token_endpoint = Column(String(500))
    userinfo_endpoint = Column(String(500))
    jwks_uri = Column(String(500))
    
    scopes = Column(String(255), default="openid profile email")
    
    user_id_claim = Column(String(100), default="sub")
    email_claim = Column(String(100), default="email")
    name_claim = Column(String(100), default="name")
    
    auto_provision_users = Column(Boolean, default=True)
    
    saml_metadata_url = Column(String(500))
    saml_entity_id = Column(String(255))
    saml_certificate = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="sso_config")
