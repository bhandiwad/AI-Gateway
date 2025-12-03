from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.app.db.models.provider_config import (
    ProviderConfig, ProviderModel, APIRoute, RoutingPolicy,
    GuardrailProfile, ProcessorDefinition
)


SERVICE_TYPES = [
    {"id": "openai", "name": "OpenAI", "description": "OpenAI GPT models", "requires_api_key": True},
    {"id": "anthropic", "name": "Anthropic", "description": "Claude models", "requires_api_key": True},
    {"id": "google", "name": "Google AI", "description": "Gemini models", "requires_api_key": True},
    {"id": "azure", "name": "Azure OpenAI", "description": "Azure-hosted OpenAI models", "requires_api_key": True},
    {"id": "aws-bedrock", "name": "AWS Bedrock", "description": "AWS Bedrock models", "requires_api_key": True},
    {"id": "mistral", "name": "Mistral AI", "description": "Mistral models", "requires_api_key": True},
    {"id": "cohere", "name": "Cohere", "description": "Cohere models", "requires_api_key": True},
    {"id": "xai", "name": "xAI (Grok)", "description": "Grok models from xAI", "requires_api_key": True},
    {"id": "meta", "name": "Meta Llama", "description": "Meta Llama models", "requires_api_key": True},
    {"id": "local-vllm", "name": "Local vLLM", "description": "Self-hosted vLLM server", "requires_api_key": False},
    {"id": "local-ollama", "name": "Local Ollama", "description": "Self-hosted Ollama server", "requires_api_key": False},
    {"id": "custom", "name": "Custom OpenAI-Compatible", "description": "Any OpenAI-compatible endpoint", "requires_api_key": True},
]


def get_service_types() -> List[Dict[str, Any]]:
    return SERVICE_TYPES


def list_providers(db: Session, tenant_id: Optional[int] = None, include_global: bool = True) -> List[ProviderConfig]:
    query = db.query(ProviderConfig)
    
    if tenant_id:
        if include_global:
            query = query.filter(
                (ProviderConfig.tenant_id == tenant_id) | (ProviderConfig.tenant_id.is_(None))
            )
        else:
            query = query.filter(ProviderConfig.tenant_id == tenant_id)
    else:
        query = query.filter(ProviderConfig.tenant_id.is_(None))
    
    return query.order_by(ProviderConfig.priority).all()


def get_provider(db: Session, provider_id: int, tenant_id: Optional[int] = None) -> Optional[ProviderConfig]:
    query = db.query(ProviderConfig).filter(ProviderConfig.id == provider_id)
    
    if tenant_id:
        query = query.filter(
            (ProviderConfig.tenant_id == tenant_id) | (ProviderConfig.tenant_id.is_(None))
        )
    
    return query.first()


def create_provider(
    db: Session,
    name: str,
    service_type: str,
    tenant_id: Optional[int] = None,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    api_key_secret_name: Optional[str] = None,
    timeout_seconds: int = 120,
    max_retries: int = 3,
    traffic_leaves_enterprise: bool = True,
    models: List[str] = None,
    rate_limit_rpm: Optional[int] = None,
    rate_limit_tpm: Optional[int] = None,
    priority: int = 0,
    config: Dict[str, Any] = None
) -> ProviderConfig:
    provider = ProviderConfig(
        tenant_id=tenant_id,
        name=name,
        display_name=display_name or name,
        description=description,
        service_type=service_type,
        endpoint_url=endpoint_url,
        api_key_secret_name=api_key_secret_name,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        traffic_leaves_enterprise=traffic_leaves_enterprise,
        models=models or [],
        rate_limit_rpm=rate_limit_rpm,
        rate_limit_tpm=rate_limit_tpm,
        priority=priority,
        config=config or {}
    )
    
    db.add(provider)
    db.commit()
    db.refresh(provider)
    
    return provider


def update_provider(
    db: Session,
    provider_id: int,
    tenant_id: Optional[int] = None,
    **kwargs
) -> Optional[ProviderConfig]:
    provider = get_provider(db, provider_id, tenant_id)
    
    if not provider:
        return None
    
    if tenant_id and provider.tenant_id is None:
        return None
    
    allowed_fields = [
        'name', 'display_name', 'description', 'service_type', 'endpoint_url',
        'api_key_secret_name', 'is_active', 'timeout_seconds', 'max_retries',
        'traffic_leaves_enterprise', 'models', 'rate_limit_rpm', 'rate_limit_tpm',
        'priority', 'config'
    ]
    
    for key, value in kwargs.items():
        if key in allowed_fields and value is not None:
            setattr(provider, key, value)
    
    db.commit()
    db.refresh(provider)
    
    return provider


def delete_provider(db: Session, provider_id: int, tenant_id: Optional[int] = None) -> bool:
    provider = get_provider(db, provider_id, tenant_id)
    
    if not provider:
        return False
    
    if tenant_id and provider.tenant_id is None:
        return False
    
    db.delete(provider)
    db.commit()
    
    return True


def add_model_to_provider(
    db: Session,
    provider_id: int,
    model_id: str,
    display_name: Optional[str] = None,
    context_length: Optional[int] = None,
    input_cost_per_1k: Optional[float] = None,
    output_cost_per_1k: Optional[float] = None,
    capabilities: List[str] = None,
    config: Dict[str, Any] = None
) -> Optional[ProviderModel]:
    provider = db.query(ProviderConfig).filter(ProviderConfig.id == provider_id).first()
    
    if not provider:
        return None
    
    model = ProviderModel(
        provider_id=provider_id,
        model_id=model_id,
        display_name=display_name or model_id,
        context_length=context_length,
        input_cost_per_1k=input_cost_per_1k,
        output_cost_per_1k=output_cost_per_1k,
        capabilities=capabilities or [],
        config=config or {}
    )
    
    db.add(model)
    db.commit()
    db.refresh(model)
    
    return model


def list_api_routes(db: Session, tenant_id: Optional[int] = None) -> List[APIRoute]:
    query = db.query(APIRoute)
    
    if tenant_id:
        query = query.filter(
            (APIRoute.tenant_id == tenant_id) | (APIRoute.tenant_id.is_(None))
        )
    else:
        query = query.filter(APIRoute.tenant_id.is_(None))
    
    return query.order_by(APIRoute.path).all()


def create_api_route(
    db: Session,
    path: str,
    tenant_id: Optional[int] = None,
    description: Optional[str] = None,
    policy_id: Optional[int] = None,
    default_provider_id: Optional[int] = None,
    default_model: Optional[str] = None,
    allowed_methods: List[str] = None,
    request_size_limit_kb: int = 10240,
    timeout_seconds: int = 120,
    rate_limit_rpm: Optional[int] = None,
    config: Dict[str, Any] = None
) -> APIRoute:
    route = APIRoute(
        tenant_id=tenant_id,
        path=path,
        description=description,
        policy_id=policy_id,
        default_provider_id=default_provider_id,
        default_model=default_model,
        allowed_methods=allowed_methods or ["POST"],
        request_size_limit_kb=request_size_limit_kb,
        timeout_seconds=timeout_seconds,
        rate_limit_rpm=rate_limit_rpm,
        config=config or {}
    )
    
    db.add(route)
    db.commit()
    db.refresh(route)
    
    return route


def update_api_route(db: Session, route_id: int, tenant_id: Optional[int] = None, **kwargs) -> Optional[APIRoute]:
    query = db.query(APIRoute).filter(APIRoute.id == route_id)
    
    if tenant_id:
        query = query.filter(
            (APIRoute.tenant_id == tenant_id) | (APIRoute.tenant_id.is_(None))
        )
    
    route = query.first()
    
    if not route:
        return None
    
    if tenant_id and route.tenant_id is None:
        return None
    
    allowed_fields = [
        'path', 'description', 'is_active', 'policy_id', 'default_provider_id',
        'default_model', 'allowed_methods', 'request_size_limit_kb',
        'timeout_seconds', 'rate_limit_rpm', 'config'
    ]
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            setattr(route, key, value)
    
    db.commit()
    db.refresh(route)
    
    return route


def delete_api_route(db: Session, route_id: int, tenant_id: Optional[int] = None) -> bool:
    query = db.query(APIRoute).filter(APIRoute.id == route_id)
    
    if tenant_id:
        query = query.filter(APIRoute.tenant_id == tenant_id)
    
    route = query.first()
    
    if not route:
        return False
    
    db.delete(route)
    db.commit()
    
    return True


def list_routing_policies(db: Session, tenant_id: Optional[int] = None) -> List[RoutingPolicy]:
    query = db.query(RoutingPolicy)
    
    if tenant_id:
        query = query.filter(
            (RoutingPolicy.tenant_id == tenant_id) | (RoutingPolicy.tenant_id.is_(None))
        )
    else:
        query = query.filter(RoutingPolicy.tenant_id.is_(None))
    
    return query.order_by(RoutingPolicy.priority).all()


def create_routing_policy(
    db: Session,
    name: str,
    tenant_id: Optional[int] = None,
    description: Optional[str] = None,
    selectors: Dict[str, Any] = None,
    profile_id: Optional[int] = None,
    allowed_providers: List[str] = None,
    allowed_models: List[str] = None,
    priority: int = 0,
    config: Dict[str, Any] = None
) -> RoutingPolicy:
    policy = RoutingPolicy(
        tenant_id=tenant_id,
        name=name,
        description=description,
        selectors=selectors or {},
        profile_id=profile_id,
        allowed_providers=allowed_providers or [],
        allowed_models=allowed_models or [],
        priority=priority,
        config=config or {}
    )
    
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    return policy


def list_guardrail_profiles(db: Session, tenant_id: Optional[int] = None) -> List[GuardrailProfile]:
    query = db.query(GuardrailProfile)
    
    if tenant_id:
        query = query.filter(
            (GuardrailProfile.tenant_id == tenant_id) | (GuardrailProfile.tenant_id.is_(None))
        )
    else:
        query = query.filter(GuardrailProfile.tenant_id.is_(None))
    
    return query.order_by(GuardrailProfile.name).all()


def create_guardrail_profile(
    db: Session,
    name: str,
    tenant_id: Optional[int] = None,
    description: Optional[str] = None,
    request_processors: List[Dict[str, Any]] = None,
    response_processors: List[Dict[str, Any]] = None,
    logging_level: str = "info",
    config: Dict[str, Any] = None
) -> GuardrailProfile:
    profile = GuardrailProfile(
        tenant_id=tenant_id,
        name=name,
        description=description,
        request_processors=request_processors or [],
        response_processors=response_processors or [],
        logging_level=logging_level,
        config=config or {}
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile


def list_processor_definitions(db: Session) -> List[ProcessorDefinition]:
    return db.query(ProcessorDefinition).order_by(ProcessorDefinition.stage, ProcessorDefinition.name).all()


def seed_processor_definitions(db: Session):
    existing = db.query(ProcessorDefinition).count()
    if existing > 0:
        return
    
    processors = [
        {
            "name": "pii_scanner",
            "display_name": "PII Scanner",
            "description": "Detects and redacts personally identifiable information",
            "processor_type": "pii",
            "stage": "request",
            "default_config": {"patterns": ["email", "phone", "ssn", "credit_card", "aadhaar", "pan"]},
            "supported_actions": ["block", "redact", "warn", "allow"]
        },
        {
            "name": "prompt_injection",
            "display_name": "Prompt Injection Detector",
            "description": "Detects and blocks prompt injection attacks",
            "processor_type": "security",
            "stage": "request",
            "default_config": {"sensitivity": "medium"},
            "supported_actions": ["block", "warn", "allow"]
        },
        {
            "name": "language_identifier",
            "display_name": "Language Identifier",
            "description": "Identifies the language of the input",
            "processor_type": "classification",
            "stage": "request",
            "default_config": {"allowed_languages": []},
            "supported_actions": ["block", "allow", "tag"]
        },
        {
            "name": "topic_classifier",
            "display_name": "Sensitive Topic Classifier",
            "description": "Classifies content into sensitive topics",
            "processor_type": "classification",
            "stage": "request",
            "default_config": {"blocked_topics": ["violence", "adult", "self_harm"]},
            "supported_actions": ["block", "warn", "allow"]
        },
        {
            "name": "request_normalizer",
            "display_name": "Request Normalizer",
            "description": "Normalizes and sanitizes request content",
            "processor_type": "transform",
            "stage": "request",
            "default_config": {"trim_whitespace": True, "normalize_unicode": True},
            "supported_actions": ["rewrite"]
        },
        {
            "name": "jailbreak_detector",
            "display_name": "Jailbreak Detector",
            "description": "Detects jailbreak attempts",
            "processor_type": "security",
            "stage": "request",
            "default_config": {"sensitivity": "high"},
            "supported_actions": ["block", "warn", "allow"]
        },
        {
            "name": "toxicity_filter",
            "display_name": "Toxicity Filter",
            "description": "Filters toxic content from responses",
            "processor_type": "content",
            "stage": "response",
            "default_config": {"threshold": 0.7},
            "supported_actions": ["block", "redact", "warn", "allow"]
        },
        {
            "name": "jailbreak_verifier",
            "display_name": "Jailbreak Response Verifier",
            "description": "Verifies responses are not jailbroken",
            "processor_type": "security",
            "stage": "response",
            "default_config": {},
            "supported_actions": ["block", "warn", "allow"]
        },
        {
            "name": "hallucination_detector",
            "display_name": "Hallucination Detector",
            "description": "Detects potential hallucinations in responses",
            "processor_type": "quality",
            "stage": "response",
            "default_config": {"confidence_threshold": 0.8},
            "supported_actions": ["block", "warn", "tag", "allow"]
        },
        {
            "name": "pii_redactor",
            "display_name": "PII Redactor",
            "description": "Redacts PII from responses",
            "processor_type": "pii",
            "stage": "response",
            "default_config": {"patterns": ["email", "phone", "ssn", "credit_card"]},
            "supported_actions": ["redact", "warn", "allow"]
        },
        {
            "name": "compliance_classifier",
            "display_name": "Compliance Classifier",
            "description": "Classifies response for regulatory compliance",
            "processor_type": "compliance",
            "stage": "response",
            "default_config": {"frameworks": ["gdpr", "hipaa", "pci_dss"]},
            "supported_actions": ["block", "warn", "tag", "allow"]
        },
        {
            "name": "financial_advice_guard",
            "display_name": "Financial Advice Guard",
            "description": "Detects unauthorized financial advice",
            "processor_type": "bfsi",
            "stage": "response",
            "default_config": {"block_investment_advice": True},
            "supported_actions": ["block", "warn", "allow"]
        }
    ]
    
    for proc_data in processors:
        proc = ProcessorDefinition(**proc_data)
        db.add(proc)
    
    db.commit()
