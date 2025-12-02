import httpx
import secrets
import hashlib
import base64
from urllib.parse import urlencode
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from backend.app.db.models.sso_config import SSOConfig, SSOProtocol
from backend.app.db.models.tenant import Tenant
from backend.app.core.security import create_access_token


class SSOService:
    def __init__(self):
        self._state_store: Dict[str, dict] = {}
        self._nonce_store: Dict[str, str] = {}
    
    def get_sso_config(self, db: Session, tenant_id: int) -> Optional[SSOConfig]:
        return db.query(SSOConfig).filter(SSOConfig.tenant_id == tenant_id).first()
    
    def get_sso_config_by_provider(self, db: Session, provider_name: str) -> Optional[SSOConfig]:
        return db.query(SSOConfig).filter(
            SSOConfig.provider_name == provider_name,
            SSOConfig.enabled == True
        ).first()
    
    def create_sso_config(
        self,
        db: Session,
        tenant_id: int,
        config_data: dict
    ) -> SSOConfig:
        sso_config = SSOConfig(
            tenant_id=tenant_id,
            **config_data
        )
        db.add(sso_config)
        db.commit()
        db.refresh(sso_config)
        return sso_config
    
    def update_sso_config(
        self,
        db: Session,
        tenant_id: int,
        config_data: dict
    ) -> Optional[SSOConfig]:
        sso_config = self.get_sso_config(db, tenant_id)
        if not sso_config:
            return None
        
        for key, value in config_data.items():
            if hasattr(sso_config, key) and value is not None:
                setattr(sso_config, key, value)
        
        db.commit()
        db.refresh(sso_config)
        return sso_config
    
    def delete_sso_config(self, db: Session, tenant_id: int) -> bool:
        sso_config = self.get_sso_config(db, tenant_id)
        if not sso_config:
            return False
        db.delete(sso_config)
        db.commit()
        return True
    
    def generate_authorization_url(
        self,
        sso_config: SSOConfig,
        redirect_uri: str
    ) -> tuple:
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b'=').decode()
        
        self._state_store[state] = {
            "tenant_id": sso_config.tenant_id,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri
        }
        self._nonce_store[nonce] = str(sso_config.tenant_id)
        
        params = {
            "client_id": sso_config.client_id,
            "response_type": "code",
            "scope": sso_config.scopes,
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        auth_url = f"{sso_config.authorization_endpoint}?{urlencode(params)}"
        return auth_url, state, nonce
    
    async def exchange_code_for_tokens(
        self,
        sso_config: SSOConfig,
        code: str,
        state: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        if state not in self._state_store:
            raise ValueError("Invalid state parameter")
        
        state_data = self._state_store.pop(state)
        code_verifier = state_data["code_verifier"]
        
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": sso_config.client_id,
            "client_secret": sso_config.client_secret,
            "code_verifier": code_verifier
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                sso_config.token_endpoint,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def get_user_info(
        self,
        sso_config: SSOConfig,
        access_token: str
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                sso_config.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get user info: {response.text}")
            
            return response.json()
    
    async def validate_id_token(
        self,
        sso_config: SSOConfig,
        id_token: str
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(sso_config.jwks_uri)
            jwks = jwks_response.json()
        
        try:
            unverified_header = jwt.get_unverified_header(id_token)
            
            rsa_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == unverified_header.get("kid"):
                    rsa_key = key
                    break
            
            if not rsa_key:
                raise ValueError("Unable to find matching key")
            
            payload = jwt.decode(
                id_token,
                rsa_key,
                algorithms=["RS256"],
                audience=sso_config.client_id,
                issuer=sso_config.issuer_url
            )
            
            return payload
            
        except JWTError as e:
            raise ValueError(f"ID token validation failed: {str(e)}")
    
    def extract_user_claims(
        self,
        sso_config: SSOConfig,
        token_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "user_id": token_payload.get(sso_config.user_id_claim),
            "email": token_payload.get(sso_config.email_claim),
            "name": token_payload.get(sso_config.name_claim),
            "raw_claims": token_payload
        }
    
    async def authenticate_sso_user(
        self,
        db: Session,
        sso_config: SSOConfig,
        code: str,
        state: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        tokens = await self.exchange_code_for_tokens(
            sso_config, code, state, redirect_uri
        )
        
        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        
        if id_token:
            user_claims = await self.validate_id_token(sso_config, id_token)
        else:
            user_claims = await self.get_user_info(sso_config, access_token)
        
        user_info = self.extract_user_claims(sso_config, user_claims)
        
        tenant = db.query(Tenant).filter(Tenant.id == sso_config.tenant_id).first()
        
        gateway_token = create_access_token(
            data={
                "sub": str(tenant.id),
                "tenant_name": tenant.name,
                "sso_user_id": user_info["user_id"],
                "sso_email": user_info["email"],
                "sso_name": user_info["name"],
                "auth_method": "sso"
            }
        )
        
        return {
            "access_token": gateway_token,
            "token_type": "bearer",
            "user": user_info,
            "tenant_id": str(tenant.id)
        }
    
    async def discover_oidc_config(self, issuer_url: str) -> Dict[str, Any]:
        discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(discovery_url)
            
            if response.status_code != 200:
                raise ValueError(f"OIDC discovery failed: {response.text}")
            
            config = response.json()
            
            return {
                "issuer_url": config.get("issuer"),
                "authorization_endpoint": config.get("authorization_endpoint"),
                "token_endpoint": config.get("token_endpoint"),
                "userinfo_endpoint": config.get("userinfo_endpoint"),
                "jwks_uri": config.get("jwks_uri"),
                "scopes_supported": config.get("scopes_supported", [])
            }


sso_service = SSOService()
