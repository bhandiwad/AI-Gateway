"""
Seed script to populate the database with comprehensive demo data.
Run with: python -m backend.scripts.seed_demo_data
"""
import os
import sys
import hashlib
import secrets
from datetime import datetime, timedelta
import random
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.db.session import SessionLocal, engine
from backend.app.db.models.tenant import Tenant
from backend.app.db.models.user import User
from backend.app.db.models.department import Department
from backend.app.db.models.team import Team
from backend.app.db.models.api_key import APIKey
from backend.app.db.models.usage_log import UsageLog
from backend.app.db.models.audit_log import AuditLog, AuditAction, AuditSeverity
from backend.app.db.models.provider_config import (
    EnhancedProviderConfig, ProviderModel, APIRoute, 
    RoutingPolicy, GuardrailProfile, ProcessorDefinition
)
from backend.app.db.models.alerts import (
    AlertConfig, AlertNotification, AlertType, AlertSeverity as AlertSev, AlertChannel
)
from backend.app.db.models.external_guardrail_provider import ExternalGuardrailProvider
from backend.app.db.models.provider_health import ProviderHealthStatus, ProviderHealthHistory


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key():
    key = f"inf_{secrets.token_urlsafe(32)}"
    return key, hash_api_key(key), key[:12]


def seed_departments(db, tenant_id: int, manager_ids: list):
    departments_data = [
        {"name": "Engineering", "code": "ENG", "description": "Software development and infrastructure", "budget_monthly": 50000, "budget_yearly": 600000, "cost_center": "CC-001"},
        {"name": "Data Science", "code": "DS", "description": "ML/AI research and data analytics", "budget_monthly": 40000, "budget_yearly": 480000, "cost_center": "CC-002"},
        {"name": "Product", "code": "PROD", "description": "Product management and design", "budget_monthly": 20000, "budget_yearly": 240000, "cost_center": "CC-003"},
        {"name": "Marketing", "code": "MKT", "description": "Marketing and communications", "budget_monthly": 15000, "budget_yearly": 180000, "cost_center": "CC-004"},
        {"name": "Customer Success", "code": "CS", "description": "Customer support and success", "budget_monthly": 25000, "budget_yearly": 300000, "cost_center": "CC-005"},
    ]
    
    departments = []
    for i, dept_data in enumerate(departments_data):
        dept = Department(
            tenant_id=tenant_id,
            manager_user_id=manager_ids[i % len(manager_ids)] if manager_ids else None,
            current_spend=random.uniform(1000, dept_data["budget_monthly"] * 0.6),
            **dept_data
        )
        db.add(dept)
        departments.append(dept)
    
    db.commit()
    for d in departments:
        db.refresh(d)
    return departments


def seed_teams(db, tenant_id: int, departments: list, lead_ids: list):
    teams_data = [
        {"dept_idx": 0, "name": "Frontend Team", "code": "FE", "description": "React/Vue development", "budget_monthly": 15000},
        {"dept_idx": 0, "name": "Backend Team", "code": "BE", "description": "Python/Go services", "budget_monthly": 18000},
        {"dept_idx": 0, "name": "Platform Team", "code": "PLAT", "description": "Infrastructure and DevOps", "budget_monthly": 12000},
        {"dept_idx": 1, "name": "ML Research", "code": "MLR", "description": "Model development", "budget_monthly": 25000},
        {"dept_idx": 1, "name": "Data Engineering", "code": "DE", "description": "Data pipelines", "budget_monthly": 10000},
        {"dept_idx": 2, "name": "Product Design", "code": "PD", "description": "UX/UI design", "budget_monthly": 8000},
        {"dept_idx": 2, "name": "Product Analytics", "code": "PA", "description": "Product insights", "budget_monthly": 7000},
        {"dept_idx": 3, "name": "Content Team", "code": "CONT", "description": "Content creation", "budget_monthly": 6000},
        {"dept_idx": 4, "name": "Support Tier 1", "code": "SUP1", "description": "First-line support", "budget_monthly": 10000},
        {"dept_idx": 4, "name": "Support Tier 2", "code": "SUP2", "description": "Technical support", "budget_monthly": 12000},
    ]
    
    teams = []
    for i, team_data in enumerate(teams_data):
        dept = departments[team_data["dept_idx"]]
        team = Team(
            tenant_id=tenant_id,
            department_id=dept.id,
            name=team_data["name"],
            code=team_data["code"],
            description=team_data["description"],
            budget_monthly=team_data["budget_monthly"],
            current_spend=random.uniform(500, team_data["budget_monthly"] * 0.5),
            lead_user_id=lead_ids[i % len(lead_ids)] if lead_ids else None,
            tags=["ai-enabled", "production"] if i % 2 == 0 else ["development"]
        )
        db.add(team)
        teams.append(team)
    
    db.commit()
    for t in teams:
        db.refresh(t)
    return teams


def seed_api_keys(db, tenant_id: int, departments: list, teams: list, user_ids: list):
    api_keys_data = [
        {"name": "Production API Key", "environment": "production", "tags": ["production", "main"]},
        {"name": "Development API Key", "environment": "development", "tags": ["development", "testing"]},
        {"name": "ML Pipeline Key", "environment": "production", "tags": ["ml", "automation"]},
        {"name": "Chat Bot Service", "environment": "production", "tags": ["chatbot", "customer-facing"]},
        {"name": "Internal Tools Key", "environment": "development", "tags": ["internal", "tools"]},
        {"name": "Analytics Service", "environment": "production", "tags": ["analytics", "reporting"]},
        {"name": "Content Generator", "environment": "production", "tags": ["content", "marketing"]},
        {"name": "Code Assistant Key", "environment": "development", "tags": ["development", "coding"]},
    ]
    
    api_keys = []
    for i, key_data in enumerate(api_keys_data):
        key, key_hash, key_prefix = generate_api_key()
        dept = departments[i % len(departments)] if departments else None
        team = teams[i % len(teams)] if teams else None
        
        api_key = APIKey(
            tenant_id=tenant_id,
            department_id=dept.id if dept else None,
            team_id=team.id if team else None,
            owner_user_id=user_ids[i % len(user_ids)] if user_ids else None,
            name=key_data["name"],
            key_hash=key_hash,
            key_prefix=key_prefix,
            environment=key_data["environment"],
            tags=key_data["tags"],
            is_active=True,
            rate_limit_override=1000 + (i * 500),
            cost_limit_daily=100.0 + (i * 50),
            cost_limit_monthly=2000.0 + (i * 500),
            last_used_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        db.add(api_key)
        api_keys.append(api_key)
    
    db.commit()
    for k in api_keys:
        db.refresh(k)
    return api_keys


def seed_providers(db, tenant_id: int):
    providers_data = [
        {
            "name": "openai",
            "display_name": "OpenAI",
            "description": "OpenAI GPT models for text generation",
            "service_type": "openai",
            "endpoint_url": "https://api.openai.com/v1",
            "priority": 1,
            "rate_limit_rpm": 3000,
            "rate_limit_tpm": 90000,
            "models": [
                {"model_id": "gpt-4-turbo", "display_name": "GPT-4 Turbo", "context_length": 128000, "input_cost": 0.01, "output_cost": 0.03},
                {"model_id": "gpt-4o", "display_name": "GPT-4o", "context_length": 128000, "input_cost": 0.005, "output_cost": 0.015},
                {"model_id": "gpt-4o-mini", "display_name": "GPT-4o Mini", "context_length": 128000, "input_cost": 0.00015, "output_cost": 0.0006},
                {"model_id": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo", "context_length": 16385, "input_cost": 0.0005, "output_cost": 0.0015},
            ]
        },
        {
            "name": "anthropic",
            "display_name": "Anthropic",
            "description": "Claude models for safe AI assistance",
            "service_type": "anthropic",
            "endpoint_url": "https://api.anthropic.com",
            "priority": 2,
            "rate_limit_rpm": 1000,
            "rate_limit_tpm": 100000,
            "models": [
                {"model_id": "claude-3-opus", "display_name": "Claude 3 Opus", "context_length": 200000, "input_cost": 0.015, "output_cost": 0.075},
                {"model_id": "claude-3-sonnet", "display_name": "Claude 3 Sonnet", "context_length": 200000, "input_cost": 0.003, "output_cost": 0.015},
                {"model_id": "claude-3-haiku", "display_name": "Claude 3 Haiku", "context_length": 200000, "input_cost": 0.00025, "output_cost": 0.00125},
            ]
        },
        {
            "name": "google",
            "display_name": "Google AI",
            "description": "Gemini models for multimodal AI",
            "service_type": "google",
            "endpoint_url": "https://generativelanguage.googleapis.com",
            "priority": 3,
            "rate_limit_rpm": 2000,
            "rate_limit_tpm": 80000,
            "models": [
                {"model_id": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro", "context_length": 1000000, "input_cost": 0.00125, "output_cost": 0.005},
                {"model_id": "gemini-1.5-flash", "display_name": "Gemini 1.5 Flash", "context_length": 1000000, "input_cost": 0.000075, "output_cost": 0.0003},
            ]
        },
        {
            "name": "azure-openai",
            "display_name": "Azure OpenAI",
            "description": "Enterprise Azure-hosted OpenAI models",
            "service_type": "azure",
            "endpoint_url": "https://your-resource.openai.azure.com",
            "priority": 4,
            "rate_limit_rpm": 2500,
            "rate_limit_tpm": 120000,
            "traffic_leaves_enterprise": False,
            "models": [
                {"model_id": "gpt-4-azure", "display_name": "GPT-4 (Azure)", "context_length": 128000, "input_cost": 0.01, "output_cost": 0.03},
            ]
        },
    ]
    
    providers = []
    for prov_data in providers_data:
        models_list = prov_data.pop("models")
        provider = EnhancedProviderConfig(
            tenant_id=tenant_id,
            **prov_data
        )
        db.add(provider)
        db.flush()
        
        for model_data in models_list:
            model = ProviderModel(
                provider_id=provider.id,
                model_id=model_data["model_id"],
                display_name=model_data["display_name"],
                context_length=model_data["context_length"],
                input_cost_per_1k=model_data["input_cost"],
                output_cost_per_1k=model_data["output_cost"],
                capabilities=["text-generation", "chat"]
            )
            db.add(model)
        
        providers.append(provider)
    
    db.commit()
    return providers


def seed_guardrail_profiles(db, tenant_id: int):
    profiles_data = [
        {
            "name": "Standard Protection",
            "description": "Default protection for general use cases",
            "request_processors": [
                {"type": "pii_detection", "action": "redact", "config": {"sensitivity": "medium"}},
                {"type": "prompt_injection", "action": "block", "config": {"threshold": 0.8}},
            ],
            "response_processors": [
                {"type": "pii_detection", "action": "redact", "config": {"sensitivity": "medium"}},
            ],
            "logging_level": "info"
        },
        {
            "name": "Healthcare Compliance",
            "description": "HIPAA-compliant processing for healthcare data",
            "request_processors": [
                {"type": "pii_detection", "action": "block", "config": {"sensitivity": "high", "types": ["SSN", "MRN", "PHI"]}},
                {"type": "prompt_injection", "action": "block", "config": {"threshold": 0.7}},
                {"type": "topic_filter", "action": "block", "config": {"blocked_topics": ["medical_advice"]}},
            ],
            "response_processors": [
                {"type": "pii_detection", "action": "redact", "config": {"sensitivity": "high"}},
                {"type": "hallucination_check", "action": "warn", "config": {}},
            ],
            "logging_level": "debug"
        },
        {
            "name": "Financial Services",
            "description": "Protection for financial data and compliance",
            "request_processors": [
                {"type": "pii_detection", "action": "redact", "config": {"types": ["credit_card", "bank_account", "SSN"]}},
                {"type": "prompt_injection", "action": "block", "config": {"threshold": 0.75}},
            ],
            "response_processors": [
                {"type": "pii_detection", "action": "redact", "config": {}},
                {"type": "content_filter", "action": "warn", "config": {"categories": ["financial_advice"]}},
            ],
            "logging_level": "info"
        },
        {
            "name": "Content Moderation",
            "description": "Strict content filtering for public-facing apps",
            "request_processors": [
                {"type": "toxicity_filter", "action": "block", "config": {"threshold": 0.5}},
                {"type": "prompt_injection", "action": "block", "config": {"threshold": 0.85}},
            ],
            "response_processors": [
                {"type": "toxicity_filter", "action": "block", "config": {"threshold": 0.6}},
                {"type": "bias_detection", "action": "warn", "config": {}},
            ],
            "logging_level": "info"
        },
        {
            "name": "Developer Mode",
            "description": "Minimal restrictions for internal development",
            "request_processors": [
                {"type": "prompt_injection", "action": "warn", "config": {"threshold": 0.9}},
            ],
            "response_processors": [],
            "logging_level": "debug"
        },
    ]
    
    profiles = []
    for prof_data in profiles_data:
        profile = GuardrailProfile(
            tenant_id=tenant_id,
            **prof_data
        )
        db.add(profile)
        profiles.append(profile)
    
    db.commit()
    return profiles


def seed_usage_logs(db, tenant_id: int, api_keys: list, departments: list, teams: list, user_ids: list):
    models = ["gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "gemini-1.5-pro"]
    providers = ["openai", "openai", "openai", "openai", "anthropic", "anthropic", "anthropic", "google"]
    endpoints = ["/v1/chat/completions", "/v1/completions", "/v1/embeddings"]
    statuses = ["success", "success", "success", "success", "success", "error", "rate_limited"]
    
    usage_logs = []
    for i in range(200):
        model_idx = random.randint(0, len(models) - 1)
        api_key = random.choice(api_keys) if api_keys else None
        dept = random.choice(departments) if departments else None
        team = random.choice(teams) if teams else None
        
        prompt_tokens = random.randint(50, 2000)
        completion_tokens = random.randint(100, 3000)
        
        cost_per_1k = [0.01, 0.005, 0.00015, 0.0005, 0.015, 0.003, 0.00025, 0.00125][model_idx]
        cost = (prompt_tokens + completion_tokens) / 1000 * cost_per_1k
        
        status = random.choice(statuses)
        
        log = UsageLog(
            tenant_id=tenant_id,
            api_key_id=api_key.id if api_key else None,
            user_id=random.choice(user_ids) if user_ids else None,
            department_id=dept.id if dept else None,
            team_id=team.id if team else None,
            request_id=str(uuid.uuid4()),
            endpoint=random.choice(endpoints),
            model=models[model_idx],
            provider=providers[model_idx],
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost,
            latency_ms=random.randint(200, 5000),
            status=status,
            error_message="Rate limit exceeded" if status == "rate_limited" else ("API error" if status == "error" else None),
            guardrail_triggered="pii_detection" if random.random() < 0.1 else None,
            guardrail_action="redact" if random.random() < 0.1 else None,
            created_at=datetime.utcnow() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
        )
        db.add(log)
        usage_logs.append(log)
    
    db.commit()
    return usage_logs


def seed_audit_logs(db, tenant_id: int, user_ids: list):
    actions = [
        (AuditAction.LOGIN, AuditSeverity.INFO, "User logged in"),
        (AuditAction.API_REQUEST, AuditSeverity.INFO, "API request processed"),
        (AuditAction.API_KEY_CREATED, AuditSeverity.INFO, "New API key created"),
        (AuditAction.USER_CREATED, AuditSeverity.INFO, "New user account created"),
        (AuditAction.POLICY_CHANGED, AuditSeverity.WARNING, "Security policy updated"),
        (AuditAction.GUARDRAIL_TRIGGERED, AuditSeverity.WARNING, "Guardrail blocked request"),
        (AuditAction.RATE_LIMIT_HIT, AuditSeverity.WARNING, "Rate limit exceeded"),
        (AuditAction.BUDGET_EXCEEDED, AuditSeverity.ERROR, "Monthly budget exceeded"),
        (AuditAction.CONFIG_CHANGED, AuditSeverity.INFO, "Configuration updated"),
        (AuditAction.ADMIN_ACTION, AuditSeverity.INFO, "Administrative action performed"),
    ]
    
    ip_addresses = ["192.168.1.100", "10.0.0.50", "172.16.0.25", "192.168.2.150", "10.10.10.10"]
    
    audit_logs = []
    for i in range(100):
        action, severity, desc = random.choice(actions)
        
        log = AuditLog(
            tenant_id=tenant_id,
            user_id=random.choice(user_ids) if user_ids else None,
            action=action,
            severity=severity,
            resource_type=random.choice(["api_key", "user", "policy", "provider", "guardrail"]),
            resource_id=str(random.randint(1, 100)),
            description=desc,
            request_id=str(uuid.uuid4())[:8],
            ip_address=random.choice(ip_addresses),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            created_at=datetime.utcnow() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23)
            )
        )
        db.add(log)
        audit_logs.append(log)
    
    db.commit()
    return audit_logs


def seed_alert_configs(db, tenant_id: int, user_ids: list):
    alerts_data = [
        {
            "name": "Cost Limit Warning",
            "alert_type": AlertType.COST_LIMIT_WARNING,
            "severity": AlertSev.WARNING,
            "conditions": {"threshold": 0.8},
            "channels": ["email", "in_app"],
        },
        {
            "name": "Cost Limit Exceeded",
            "alert_type": AlertType.COST_LIMIT_EXCEEDED,
            "severity": AlertSev.ERROR,
            "conditions": {"threshold": 1.0},
            "channels": ["email", "slack", "in_app"],
        },
        {
            "name": "Provider Health Alert",
            "alert_type": AlertType.PROVIDER_UNHEALTHY,
            "severity": AlertSev.ERROR,
            "conditions": {"min_consecutive_failures": 3},
            "channels": ["email", "slack"],
        },
        {
            "name": "High Error Rate",
            "alert_type": AlertType.HIGH_ERROR_RATE,
            "severity": AlertSev.WARNING,
            "conditions": {"error_rate_threshold": 0.1},
            "channels": ["in_app"],
        },
        {
            "name": "Rate Limit Warning",
            "alert_type": AlertType.RATE_LIMIT_WARNING,
            "severity": AlertSev.INFO,
            "conditions": {"threshold": 0.9},
            "channels": ["in_app"],
        },
    ]
    
    alert_configs = []
    for alert_data in alerts_data:
        config = AlertConfig(
            tenant_id=tenant_id,
            created_by=user_ids[0] if user_ids else None,
            **alert_data
        )
        db.add(config)
        alert_configs.append(config)
    
    db.commit()
    return alert_configs


def seed_alert_notifications(db, tenant_id: int, alert_configs: list):
    notifications = []
    
    for config in alert_configs:
        for i in range(random.randint(2, 8)):
            notif = AlertNotification(
                alert_config_id=config.id,
                tenant_id=tenant_id,
                alert_type=config.alert_type,
                severity=config.severity,
                title=f"{config.name} - Alert #{i+1}",
                message=f"Alert triggered: {config.name}. Please review the situation.",
                context={"value": random.uniform(0.7, 1.0), "limit": 1.0},
                channels_sent=config.channels,
                is_read=random.choice([True, False]),
                is_acknowledged=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
            )
            db.add(notif)
            notifications.append(notif)
    
    db.commit()
    return notifications


def seed_external_guardrail_providers(db, tenant_id: int):
    providers_data = [
        {
            "name": "AWS Bedrock Guardrails",
            "provider_type": "aws_bedrock",
            "description": "AWS Bedrock content moderation and safety filters",
            "api_endpoint": "https://bedrock.us-east-1.amazonaws.com",
            "region": "us-east-1",
            "is_enabled": True,
            "custom_config": {"guardrail_id": "demo-guardrail"},
            "capabilities": ["content_filter", "pii_detection", "topic_filter"],
            "priority": 1
        },
        {
            "name": "Azure Content Safety",
            "provider_type": "azure_content_safety",
            "description": "Microsoft Azure AI Content Safety service",
            "api_endpoint": "https://your-resource.cognitiveservices.azure.com",
            "is_enabled": True,
            "custom_config": {"api_version": "2024-02-15-preview"},
            "capabilities": ["hate_speech", "violence", "self_harm", "sexual"],
            "priority": 2
        },
        {
            "name": "Lakera Guard",
            "provider_type": "lakera",
            "description": "Lakera Guard for prompt injection and jailbreak detection",
            "api_endpoint": "https://api.lakera.ai",
            "is_enabled": False,
            "custom_config": {},
            "capabilities": ["prompt_injection", "jailbreak_detection"],
            "priority": 3
        },
    ]
    
    providers = []
    for prov_data in providers_data:
        provider = ExternalGuardrailProvider(
            tenant_id=tenant_id,
            **prov_data
        )
        db.add(provider)
        providers.append(provider)
    
    db.commit()
    return providers


def seed_api_routes(db, tenant_id: int, providers: list, profiles: list):
    routes_data = [
        {"path": "/v1/chat/completions", "description": "Chat completions endpoint", "rate_limit_rpm": 1000},
        {"path": "/v1/completions", "description": "Text completions endpoint", "rate_limit_rpm": 500},
        {"path": "/v1/embeddings", "description": "Text embeddings endpoint", "rate_limit_rpm": 2000},
        {"path": "/v1/images/generations", "description": "Image generation endpoint", "rate_limit_rpm": 100},
        {"path": "/v1/audio/transcriptions", "description": "Audio transcription endpoint", "rate_limit_rpm": 200},
    ]
    
    routes = []
    for i, route_data in enumerate(routes_data):
        route = APIRoute(
            tenant_id=tenant_id,
            default_provider_id=providers[i % len(providers)].id if providers else None,
            default_model="gpt-4o",
            **route_data
        )
        db.add(route)
        routes.append(route)
    
    db.commit()
    return routes


def seed_provider_health(db, tenant_id: int, providers: list):
    for provider in providers:
        is_healthy = random.choice([True, True, True, False])
        circuit_state = "closed" if random.random() > 0.1 else "open"
        
        health = ProviderHealthStatus(
            tenant_id=tenant_id,
            provider_name=provider.name,
            provider_config_id=provider.id,
            is_healthy=is_healthy,
            circuit_state=circuit_state,
            consecutive_failures=0 if circuit_state == "closed" else random.randint(1, 5),
            consecutive_successes=random.randint(5, 20) if circuit_state == "closed" else 0,
            failure_count=random.randint(0, 50),
            success_count=random.randint(500, 5000),
            total_requests=random.randint(1000, 10000),
            total_failures=random.randint(10, 100),
            avg_latency_ms=random.uniform(100, 500),
            active_requests=random.randint(0, 10),
            last_success_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
            last_failure_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)) if random.random() < 0.5 else None,
            last_health_check_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 10))
        )
        db.add(health)
        db.flush()
        
        event_types = ["success", "failure", "circuit_opened", "circuit_closed", "health_check_passed"]
        for j in range(24):
            history = ProviderHealthHistory(
                provider_status_id=health.id,
                tenant_id=tenant_id,
                provider_name=provider.name,
                event_type=random.choice(event_types),
                circuit_state_before="closed",
                circuit_state_after="closed",
                failure_count=random.randint(0, 10),
                success_count=random.randint(100, 500),
                latency_ms=random.uniform(80, 600),
                created_at=datetime.utcnow() - timedelta(hours=j)
            )
            db.add(history)
    
    db.commit()


def seed_processor_definitions(db):
    existing = db.query(ProcessorDefinition).first()
    if existing:
        return
    
    processors_data = [
        {"name": "pii_detection", "display_name": "PII Detection", "processor_type": "security", "stage": "both", "description": "Detects and redacts personally identifiable information"},
        {"name": "prompt_injection", "display_name": "Prompt Injection Detection", "processor_type": "security", "stage": "request", "description": "Detects prompt injection attempts"},
        {"name": "toxicity_filter", "display_name": "Toxicity Filter", "processor_type": "content", "stage": "both", "description": "Filters toxic and harmful content"},
        {"name": "topic_filter", "display_name": "Topic Filter", "processor_type": "content", "stage": "both", "description": "Blocks specific topics"},
        {"name": "content_filter", "display_name": "Content Filter", "processor_type": "content", "stage": "response", "description": "General content filtering"},
        {"name": "hallucination_check", "display_name": "Hallucination Detection", "processor_type": "quality", "stage": "response", "description": "Checks for factual accuracy"},
        {"name": "bias_detection", "display_name": "Bias Detection", "processor_type": "fairness", "stage": "response", "description": "Detects biased content"},
        {"name": "rate_limiter", "display_name": "Rate Limiter", "processor_type": "traffic", "stage": "request", "description": "Enforces rate limits"},
    ]
    
    for proc_data in processors_data:
        processor = ProcessorDefinition(**proc_data)
        db.add(processor)
    
    db.commit()


def main():
    print("Starting demo data seeding...")
    db = SessionLocal()
    
    try:
        tenant = db.query(Tenant).filter(Tenant.id == 1).first()
        if not tenant:
            print("No tenant found with ID 1. Please create a tenant first.")
            return
        
        tenant_id = tenant.id
        print(f"Using tenant: {tenant.name} (ID: {tenant_id})")
        
        users = db.query(User).filter(User.tenant_id == tenant_id).all()
        user_ids = [u.id for u in users]
        manager_ids = [u.id for u in users if u.role in ["ADMIN", "MANAGER"]]
        print(f"Found {len(users)} users, {len(manager_ids)} managers")
        
        print("Seeding processor definitions...")
        seed_processor_definitions(db)
        
        print("Seeding departments...")
        departments = seed_departments(db, tenant_id, manager_ids)
        print(f"Created {len(departments)} departments")
        
        print("Seeding teams...")
        teams = seed_teams(db, tenant_id, departments, user_ids)
        print(f"Created {len(teams)} teams")
        
        print("Seeding API keys...")
        api_keys = seed_api_keys(db, tenant_id, departments, teams, user_ids)
        print(f"Created {len(api_keys)} API keys")
        
        print("Seeding providers...")
        providers = seed_providers(db, tenant_id)
        print(f"Created {len(providers)} providers with models")
        
        print("Seeding guardrail profiles...")
        profiles = seed_guardrail_profiles(db, tenant_id)
        print(f"Created {len(profiles)} guardrail profiles")
        
        print("Seeding usage logs...")
        usage_logs = seed_usage_logs(db, tenant_id, api_keys, departments, teams, user_ids)
        print(f"Created {len(usage_logs)} usage logs")
        
        print("Seeding audit logs...")
        audit_logs = seed_audit_logs(db, tenant_id, user_ids)
        print(f"Created {len(audit_logs)} audit logs")
        
        print("Seeding alert configurations...")
        alert_configs = seed_alert_configs(db, tenant_id, user_ids)
        print(f"Created {len(alert_configs)} alert configs")
        
        print("Seeding alert notifications...")
        notifications = seed_alert_notifications(db, tenant_id, alert_configs)
        print(f"Created {len(notifications)} notifications")
        
        print("Seeding external guardrail providers...")
        ext_providers = seed_external_guardrail_providers(db, tenant_id)
        print(f"Created {len(ext_providers)} external guardrail providers")
        
        print("Seeding API routes...")
        routes = seed_api_routes(db, tenant_id, providers, profiles)
        print(f"Created {len(routes)} API routes")
        
        print("Seeding provider health data...")
        seed_provider_health(db, tenant_id, providers)
        print("Provider health data created")
        
        print("\n✓ Demo data seeding completed successfully!")
        print("\nSummary:")
        print(f"  - Departments: {len(departments)}")
        print(f"  - Teams: {len(teams)}")
        print(f"  - API Keys: {len(api_keys)}")
        print(f"  - Providers: {len(providers)}")
        print(f"  - Guardrail Profiles: {len(profiles)}")
        print(f"  - Usage Logs: {len(usage_logs)}")
        print(f"  - Audit Logs: {len(audit_logs)}")
        print(f"  - Alert Configs: {len(alert_configs)}")
        print(f"  - Notifications: {len(notifications)}")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
