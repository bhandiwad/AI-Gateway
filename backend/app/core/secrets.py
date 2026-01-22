"""
Secrets Management Service
Supports HashiCorp Vault with fallback to environment variables.

Usage:
    from backend.app.core.secrets import secrets_manager
    
    # Get a secret (tries Vault first, then env)
    api_key = await secrets_manager.get_secret("OPENAI_API_KEY")
    
    # Get multiple secrets
    secrets = await secrets_manager.get_secrets(["OPENAI_API_KEY", "ANTHROPIC_API_KEY"])
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from functools import lru_cache
import structlog

logger = structlog.get_logger()


class SecretsManager:
    """
    Unified secrets manager with support for:
    - HashiCorp Vault (primary, if configured)
    - Environment variables (fallback)
    - Local cache with TTL
    """
    
    def __init__(self):
        self._vault_client = None
        self._vault_enabled = False
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._initialized = False
    
    async def initialize(self):
        """Initialize the secrets manager."""
        if self._initialized:
            return
        
        vault_addr = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")
        vault_role_id = os.getenv("VAULT_ROLE_ID")
        vault_secret_id = os.getenv("VAULT_SECRET_ID")
        
        if vault_addr and (vault_token or (vault_role_id and vault_secret_id)):
            await self._init_vault(
                vault_addr,
                vault_token,
                vault_role_id,
                vault_secret_id
            )
        else:
            logger.info(
                "vault_not_configured",
                message="Using environment variables for secrets"
            )
        
        self._initialized = True
    
    async def _init_vault(
        self,
        addr: str,
        token: Optional[str],
        role_id: Optional[str],
        secret_id: Optional[str]
    ):
        """Initialize HashiCorp Vault client."""
        try:
            import hvac
            
            self._vault_client = hvac.Client(url=addr)
            
            if token:
                self._vault_client.token = token
            elif role_id and secret_id:
                # AppRole authentication
                response = self._vault_client.auth.approle.login(
                    role_id=role_id,
                    secret_id=secret_id
                )
                self._vault_client.token = response["auth"]["client_token"]
            
            if self._vault_client.is_authenticated():
                self._vault_enabled = True
                logger.info(
                    "vault_connected",
                    address=addr,
                    auth_method="token" if token else "approle"
                )
            else:
                logger.warning("vault_authentication_failed")
                
        except ImportError:
            logger.warning(
                "vault_hvac_not_installed",
                message="Install hvac package: pip install hvac"
            )
        except Exception as e:
            logger.error("vault_connection_failed", error=str(e))
    
    async def get_secret(
        self,
        key: str,
        path: Optional[str] = None,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret value.
        
        Args:
            key: Secret key name (e.g., "OPENAI_API_KEY")
            path: Vault path (default: "secret/data/ai-gateway")
            default: Default value if not found
            
        Returns:
            Secret value or default
        """
        # Check cache first
        cached = self._get_from_cache(key)
        if cached is not None:
            return cached
        
        value = None
        
        # Try Vault first
        if self._vault_enabled:
            value = await self._get_from_vault(key, path)
        
        # Fallback to environment variable
        if value is None:
            value = os.getenv(key, default)
        
        # Cache the result
        if value is not None:
            self._set_cache(key, value)
        
        return value
    
    async def get_secrets(
        self,
        keys: List[str],
        path: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """Get multiple secrets at once."""
        results = {}
        for key in keys:
            results[key] = await self.get_secret(key, path)
        return results
    
    async def _get_from_vault(
        self,
        key: str,
        path: Optional[str] = None
    ) -> Optional[str]:
        """Fetch secret from Vault."""
        if not self._vault_client:
            return None
        
        path = path or os.getenv("VAULT_SECRET_PATH", "secret/data/ai-gateway")
        
        try:
            # KV v2 secrets engine
            response = self._vault_client.secrets.kv.v2.read_secret_version(
                path=path.replace("secret/data/", ""),
                mount_point="secret"
            )
            
            data = response.get("data", {}).get("data", {})
            value = data.get(key)
            
            if value:
                logger.debug("secret_fetched_from_vault", key=key)
            
            return value
            
        except Exception as e:
            logger.warning(
                "vault_secret_fetch_failed",
                key=key,
                error=str(e)
            )
            return None
    
    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get value from local cache if not expired."""
        import time
        
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self._cache_ttl:
                return entry["value"]
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: str):
        """Set value in local cache."""
        import time
        self._cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def clear_cache(self):
        """Clear the secrets cache."""
        self._cache.clear()
        logger.info("secrets_cache_cleared")
    
    async def set_secret(
        self,
        key: str,
        value: str,
        path: Optional[str] = None
    ) -> bool:
        """
        Set a secret in Vault.
        
        Args:
            key: Secret key name
            value: Secret value
            path: Vault path
            
        Returns:
            True if successful, False otherwise
        """
        if not self._vault_enabled:
            logger.warning(
                "vault_not_enabled",
                message="Cannot set secret - Vault not configured"
            )
            return False
        
        path = path or os.getenv("VAULT_SECRET_PATH", "ai-gateway")
        
        try:
            # Read existing secrets first
            try:
                existing = self._vault_client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point="secret"
                )
                data = existing.get("data", {}).get("data", {})
            except Exception:
                data = {}
            
            # Update with new secret
            data[key] = value
            
            self._vault_client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point="secret"
            )
            
            # Update cache
            self._set_cache(key, value)
            
            logger.info("secret_stored_in_vault", key=key)
            return True
            
        except Exception as e:
            logger.error("vault_secret_store_failed", key=key, error=str(e))
            return False
    
    @property
    def is_vault_enabled(self) -> bool:
        """Check if Vault is enabled and connected."""
        return self._vault_enabled
    
    async def health_check(self) -> Dict[str, Any]:
        """Check secrets manager health."""
        status = {
            "vault_enabled": self._vault_enabled,
            "vault_connected": False,
            "cache_size": len(self._cache),
            "fallback_to_env": True
        }
        
        if self._vault_enabled and self._vault_client:
            try:
                status["vault_connected"] = self._vault_client.is_authenticated()
            except Exception:
                status["vault_connected"] = False
        
        return status


# Global singleton instance
secrets_manager = SecretsManager()


async def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret."""
    if not secrets_manager._initialized:
        await secrets_manager.initialize()
    return await secrets_manager.get_secret(key, default=default)
