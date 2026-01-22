"""
Hierarchical Guardrail Profile Resolution Service

Resolves the appropriate guardrail profile based on:
1. Route-based Policy (with selector matching)
2. API Key override
3. Department default
4. Team default
5. Tenant default
6. System default (None - uses legacy guardrails_service)
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session, joinedload
import structlog

from backend.app.db.models.provider_config import GuardrailProfile, RoutingPolicy, APIRoute
from backend.app.db.models.api_key import APIKey
from backend.app.db.models.tenant import Tenant
from backend.app.db.models.department import Department
from backend.app.db.models.team import Team


logger = structlog.get_logger()


class GuardrailResolver:
    """Hierarchical guardrail profile resolution with selector matching."""
    
    def __init__(self):
        self._route_cache = {}  # Cache for route lookups
    
    def resolve_profile(
        self,
        db: Session,
        request_path: str,
        api_key: APIKey,
        tenant: Tenant,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[GuardrailProfile]:
        """
        Resolve the guardrail profile to apply based on hierarchy.
        
        Resolution Order (highest priority first):
        1. Route-based Policy (with selector matching)
        2. API Key override
        3. Team default (if api_key has team_id)
        4. Department default (if api_key has department_id)
        5. Tenant default
        6. System default (None - falls back to legacy guardrails)
        
        Args:
            db: Database session
            request_path: The API request path (e.g., /v1/chat/completions)
            api_key: The API key making the request
            tenant: The tenant the request belongs to
            context: Additional context for selector matching
            
        Returns:
            GuardrailProfile if found, None otherwise (use legacy guardrails)
        """
        context = context or {}
        
        context.setdefault("department_id", api_key.department_id)
        context.setdefault("team_id", api_key.team_id)
        context.setdefault("api_key_tags", api_key.tags or [])
        
        # OPTIMIZATION: Eager load ALL relationships in ONE query
        api_key_full = db.query(APIKey).options(
            joinedload(APIKey.guardrail_profile),
            joinedload(APIKey.team).joinedload(Team.guardrail_profile),
            joinedload(APIKey.department).joinedload(Department.guardrail_profile)
        ).filter(APIKey.id == api_key.id).first()
        
        if not api_key_full:
            return None
        
        # 1. Route-based resolution
        profile = self._resolve_from_route(db, request_path, tenant.id, context)
        if profile:
            return profile
        
        # 2. API Key override (already loaded)
        if api_key_full.guardrail_profile:
            return api_key_full.guardrail_profile
        
        # 3. Team default (already loaded)
        if api_key_full.team and api_key_full.team.guardrail_profile:
            return api_key_full.team.guardrail_profile
        
        # 4. Department default (already loaded)
        if api_key_full.department and api_key_full.department.guardrail_profile:
            return api_key_full.department.guardrail_profile
        
        # 5. Tenant default
        if tenant.guardrail_profile_id:
            profile = db.query(GuardrailProfile).filter(
                GuardrailProfile.id == tenant.guardrail_profile_id,
                GuardrailProfile.is_active == True
            ).first()
            if profile:
                return profile
        
        return None
    
    def _resolve_from_route(
        self,
        db: Session,
        request_path: str,
        tenant_id: int,
        context: Dict[str, Any]
    ) -> Optional[GuardrailProfile]:
        """Match request to route and resolve profile via policy."""
        route = self._match_route(db, request_path, tenant_id)
        if not route:
            return None
        
        if not route.policy_id:
            return None
        
        # OPTIMIZATION: Eager load policy with profile
        policy = db.query(RoutingPolicy).options(
            joinedload(RoutingPolicy.profile)
        ).filter(
            RoutingPolicy.id == route.policy_id,
            RoutingPolicy.is_active == True
        ).first()
        
        if not policy:
            return None
        
        if not self._evaluate_selectors(policy.selectors, context):
            return None
        
        if not policy.profile_id:
            return None
        
        # Profile already loaded via joinedload
        if policy.profile and policy.profile.is_active:
            return policy.profile
        
        return None
    
    def _match_route(
        self,
        db: Session,
        request_path: str,
        tenant_id: int
    ) -> Optional[APIRoute]:
        """
        Match the request path to an API route.
        Routes are matched by priority (higher first), then by path specificity.
        """
        routes = db.query(APIRoute).filter(
            APIRoute.is_active == True,
            (APIRoute.tenant_id == tenant_id) | (APIRoute.tenant_id == None)
        ).order_by(APIRoute.priority.desc()).all()
        
        for route in routes:
            if self._path_matches(request_path, route.path):
                return route
        
        return None
    
    def _path_matches(self, request_path: str, route_path: str) -> bool:
        """
        Check if request path matches route pattern.
        Supports exact match and prefix matching with wildcards.
        """
        request_path = request_path.rstrip('/')
        route_path = route_path.rstrip('/')
        
        if request_path == route_path:
            return True
        
        if route_path.endswith('/*'):
            prefix = route_path[:-2]
            return request_path.startswith(prefix)
        
        if route_path.endswith('/**'):
            prefix = route_path[:-3]
            return request_path.startswith(prefix)
        
        return request_path.startswith(route_path + '/')
    
    def _evaluate_selectors(
        self,
        selectors: Optional[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if request context matches policy selectors.
        
        Selector types:
        - department_id: List of allowed department IDs
        - team_id: List of allowed team IDs
        - jwt_claims: Dict of required JWT claim values
        - api_key_tags: List of required tags (any match)
        - environments: List of allowed environments
        
        Returns True if all selectors match (AND logic).
        Empty selectors = match all.
        """
        if not selectors:
            return True
        
        if "department_id" in selectors:
            allowed_depts = selectors["department_id"]
            if isinstance(allowed_depts, list):
                if context.get("department_id") not in allowed_depts:
                    return False
        
        if "team_id" in selectors:
            allowed_teams = selectors["team_id"]
            if isinstance(allowed_teams, list):
                if context.get("team_id") not in allowed_teams:
                    return False
        
        if "jwt_claims" in selectors:
            required_claims = selectors["jwt_claims"]
            actual_claims = context.get("jwt_claims", {})
            for key, expected_value in required_claims.items():
                if actual_claims.get(key) != expected_value:
                    return False
        
        if "api_key_tags" in selectors:
            required_tags = selectors["api_key_tags"]
            actual_tags = context.get("api_key_tags", [])
            if not any(tag in actual_tags for tag in required_tags):
                return False
        
        if "environments" in selectors:
            allowed_envs = selectors["environments"]
            if context.get("environment") not in allowed_envs:
                return False
        
        return True
    
    def resolve_allowed_models(
        self,
        db: Session,
        request_path: str,
        api_key: APIKey,
        tenant: Tenant
    ) -> Optional[List[str]]:
        """
        Resolve allowed models based on hierarchy.
        
        Resolution Order (first non-empty wins):
        1. Route policy allowed_models
        2. API Key allowed_models_override
        3. Team allowed_models
        4. Department allowed_models
        5. Tenant allowed_models
        6. None (all models allowed)
        """
        route = self._match_route(db, request_path, tenant.id)
        if route and route.policy_id:
            policy = db.query(RoutingPolicy).filter(
                RoutingPolicy.id == route.policy_id,
                RoutingPolicy.is_active == True
            ).first()
            if policy and policy.allowed_models:
                return policy.allowed_models
        
        if api_key.allowed_models_override:
            return api_key.allowed_models_override
        
        # OPTIMIZATION: Eager load relationships
        api_key_full = db.query(APIKey).options(
            joinedload(APIKey.team),
            joinedload(APIKey.department)
        ).filter(APIKey.id == api_key.id).first()
        
        if not api_key_full:
            return None
        
        if api_key_full.team and api_key_full.team.allowed_models:
            return api_key_full.team.allowed_models
        
        if api_key_full.department and api_key_full.department.allowed_models:
            return api_key_full.department.allowed_models
        
        if tenant.allowed_models:
            return tenant.allowed_models
        
        return None
    
    def resolve_allowed_providers(
        self,
        db: Session,
        request_path: str,
        api_key: APIKey,
        tenant: Tenant
    ) -> Optional[List[str]]:
        """
        Resolve allowed providers based on hierarchy.
        Same resolution order as allowed_models.
        """
        route = self._match_route(db, request_path, tenant.id)
        if route and route.policy_id:
            policy = db.query(RoutingPolicy).filter(
                RoutingPolicy.id == route.policy_id,
                RoutingPolicy.is_active == True
            ).first()
            if policy and policy.allowed_providers:
                return policy.allowed_providers
        
        if api_key.allowed_providers_override:
            return api_key.allowed_providers_override
        
        # OPTIMIZATION: Eager load relationships
        api_key_full = db.query(APIKey).options(
            joinedload(APIKey.team),
            joinedload(APIKey.department)
        ).filter(APIKey.id == api_key.id).first()
        
        if not api_key_full:
            return None
        
        if api_key_full.team and api_key_full.team.allowed_providers:
            return api_key_full.team.allowed_providers
        
        if api_key_full.department and api_key_full.department.allowed_providers:
            return api_key_full.department.allowed_providers
        
        if hasattr(tenant, 'allowed_providers') and tenant.allowed_providers:
            return tenant.allowed_providers
        
        return None


guardrail_resolver = GuardrailResolver()
