from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class SSOProtocol(str, Enum):
    OIDC = "oidc"
    SAML = "saml"


class SSOConfigCreate(BaseModel):
    enabled: bool = True
    protocol: SSOProtocol = SSOProtocol.OIDC
    provider_name: str
    client_id: str
    client_secret: str
    issuer_url: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    scopes: str = "openid profile email"
    user_id_claim: str = "sub"
    email_claim: str = "email"
    name_claim: str = "name"
    auto_provision_users: bool = True


class SSOConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    provider_name: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    issuer_url: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    scopes: Optional[str] = None
    user_id_claim: Optional[str] = None
    email_claim: Optional[str] = None
    name_claim: Optional[str] = None
    auto_provision_users: Optional[bool] = None


class SSOConfigResponse(BaseModel):
    id: int
    tenant_id: int
    enabled: bool
    protocol: str
    provider_name: Optional[str]
    client_id: Optional[str]
    issuer_url: Optional[str]
    authorization_endpoint: Optional[str]
    token_endpoint: Optional[str]
    userinfo_endpoint: Optional[str]
    scopes: Optional[str]
    user_id_claim: str
    email_claim: str
    name_claim: str
    auto_provision_users: bool

    class Config:
        from_attributes = True


class SSOLoginInitiate(BaseModel):
    provider_name: str
    redirect_uri: str


class SSOLoginCallback(BaseModel):
    code: str
    state: str
    redirect_uri: str


class SSOAuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]
    tenant_id: str


class OIDCDiscoveryRequest(BaseModel):
    issuer_url: str


class OIDCDiscoveryResponse(BaseModel):
    issuer_url: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    scopes_supported: List[str]
