import httpx
import secrets
import hashlib
import base64
import json
from urllib.parse import urlencode
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.app.db.models.sso_config import SSOConfig, SSOProtocol
from backend.app.db.models.tenant import Tenant
from backend.app.core.security import create_access_token
from backend.app.core.config import settings


class SSOService:
    STATE_EXPIRY_SECONDS = 600
    
    def __init__(self):
        self._redis = None
        self._local_store: Dict[str, str] = {}
    
    async def _get_redis(self):
        if self._redis is None and settings.REDIS_URL:
            import redis.asyncio as aioredis
            self._redis = await aioredis.from_url(settings.REDIS_URL)
        return self._redis
    
    async def _store_state(self, key: str, data: dict) -> None:
        serialized = json.dumps(data)
        redis_client = await self._get_redis()
        if redis_client:
            await redis_client.setex(
                f"sso_state:{key}",
                self.STATE_EXPIRY_SECONDS,
                serialized
            )
        else:
            self._local_store[key] = serialized
    
    async def _get_state(self, key: str) -> Optional[dict]:
        redis_client = await self._get_redis()
        if redis_client:
            data = await redis_client.get(f"sso_state:{key}")
            if data:
                await redis_client.delete(f"sso_state:{key}")
                return json.loads(data)
        else:
            data = self._local_store.pop(key, None)
            if data:
                return json.loads(data)
        return None
    
    def get_sso_config(self, db: Session, tenant_id: int) -> Optional[SSOConfig]:
        return db.query(SSOConfig).filter(SSOConfig.tenant_id == tenant_id).first()
    
    def get_sso_config_by_provider(self, db: Session, provider_name: str) -> Optional[SSOConfig]:
        return db.query(SSOConfig).filter(
            SSOConfig.provider_name == provider_name,
            SSOConfig.enabled == True
        ).first()
    
    def get_tenant_by_domain(self, db: Session, domain: str) -> Optional[Tenant]:
        return db.query(Tenant).filter(
            Tenant.email.ilike(f"%@{domain}")
        ).first()
    
    def get_sso_config_by_tenant_name(self, db: Session, tenant_name: str) -> Optional[SSOConfig]:
        tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
        if tenant:
            return self.get_sso_config(db, tenant.id)
        return None
    
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
    
    async def generate_authorization_url(
        self,
        sso_config: SSOConfig,
        redirect_uri: str,
        final_redirect: Optional[str] = None
    ) -> tuple:
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b'=').decode()
        
        state_data = {
            "tenant_id": sso_config.tenant_id,
            "provider_name": sso_config.provider_name,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
            "nonce": nonce,
            "final_redirect": final_redirect or redirect_uri,
            "created_at": datetime.utcnow().isoformat()
        }
        await self._store_state(state, state_data)
        
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
        return auth_url, state
    
    async def exchange_code_for_tokens(
        self,
        sso_config: SSOConfig,
        code: str,
        state: str,
        expected_provider: str
    ) -> Dict[str, Any]:
        state_data = await self._get_state(state)
        if not state_data:
            raise ValueError("Invalid or expired state parameter")
        
        created_at = datetime.fromisoformat(state_data["created_at"])
        if datetime.utcnow() - created_at > timedelta(seconds=self.STATE_EXPIRY_SECONDS):
            raise ValueError("State has expired")
        
        stored_provider = state_data.get("provider_name")
        if stored_provider != expected_provider:
            raise ValueError("Provider mismatch - possible replay attack")
        
        code_verifier = state_data["code_verifier"]
        redirect_uri = state_data["redirect_uri"]
        nonce = state_data["nonce"]
        final_redirect = state_data.get("final_redirect", redirect_uri)
        
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
            
            tokens = response.json()
            tokens["_nonce"] = nonce
            tokens["_final_redirect"] = final_redirect
            tokens["_tenant_id"] = state_data["tenant_id"]
            return tokens
    
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
        id_token: str,
        expected_nonce: Optional[str] = None
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
            
            if expected_nonce and payload.get("nonce") != expected_nonce:
                raise ValueError("Nonce mismatch - possible replay attack")
            
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
        provider_name: str
    ) -> Dict[str, Any]:
        tokens = await self.exchange_code_for_tokens(
            sso_config, code, state, provider_name
        )
        
        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        expected_nonce = tokens.get("_nonce")
        final_redirect = tokens.get("_final_redirect")
        
        if id_token:
            user_claims = await self.validate_id_token(sso_config, id_token, expected_nonce)
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
            "tenant_id": str(tenant.id),
            "redirect_to": final_redirect
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
    
    def list_enabled_providers(self, db: Session) -> list:
        configs = db.query(SSOConfig).filter(SSOConfig.enabled == True).all()
        return [
            {
                "provider_name": cfg.provider_name,
                "tenant_id": cfg.tenant_id
            }
            for cfg in configs
        ]


sso_service = SSOService()
