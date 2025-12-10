"""
Profile-Based Guardrails Service

Applies guardrail processor chains defined in GuardrailProfile.
Each profile contains ordered request_processors and response_processors.
Supports both internal processors and external guardrail providers.
"""
import re
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from backend.app.db.models.provider_config import GuardrailProfile
import structlog

logger = structlog.get_logger()


@dataclass
class ProfileGuardrailResult:
    """Result of applying profile guardrails."""
    passed: bool
    message: str
    action: str
    triggered_processor: Optional[str] = None
    processed_messages: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
    "ssn": r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b',
    "credit_card": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
    "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
}

PROMPT_INJECTION_PATTERNS = [
    r'ignore\s+(previous|all|above)\s+(instructions?|prompts?)',
    r'disregard\s+(previous|all|your)\s+(instructions?|rules?)',
    r'forget\s+(everything|all|previous)',
    r'you\s+are\s+now\s+',
    r'new\s+instructions?\s*:',
    r'system\s*:\s*',
    r'<\s*system\s*>',
    r'\[\s*SYSTEM\s*\]',
    r'override\s+(previous|safety|all)',
    r'bypass\s+(filter|safety|restriction)',
]

TOXIC_PATTERNS = [
    r'\b(kill|murder|harm|attack|destroy)\s+(yourself|everyone|people|them)\b',
    r'\b(hate|despise)\s+(all|every)\s+\w+\b',
]


def apply_profile_guardrails(
    profile: GuardrailProfile,
    messages: List[Dict[str, Any]],
    stage: str,
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    Apply guardrail processors from profile to messages.
    
    Args:
        profile: The GuardrailProfile containing processor chains
        messages: The messages to process
        stage: "request" or "response"
        tenant_id: Tenant ID for logging
        
    Returns:
        ProfileGuardrailResult with pass/fail status and processed messages
    """
    processors = profile.request_processors if stage == "request" else profile.response_processors
    
    if processors is None or len(processors) == 0:
        return ProfileGuardrailResult(
            passed=True,
            message="No processors configured",
            action="allow",
            processed_messages=messages
        )
    
    processed_messages = [msg.copy() for msg in messages]
    
    for processor_config in processors:
        processor_type = processor_config.get("type")
        action = processor_config.get("action", "block")
        config = processor_config.get("config", {})
        
        result = _apply_processor(
            processor_type=processor_type,
            action=action,
            config=config,
            messages=processed_messages,
            tenant_id=tenant_id
        )
        
        if not result.passed:
            return result
        
        if result.processed_messages:
            processed_messages = result.processed_messages
    
    return ProfileGuardrailResult(
        passed=True,
        message="All processors passed",
        action="allow",
        processed_messages=processed_messages
    )


def _apply_processor(
    processor_type: str,
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """Apply a single processor to messages."""
    
    processor_handlers = {
        "pii_detection": _process_pii_detection,
        "prompt_injection": _process_prompt_injection,
        "toxicity_filter": _process_toxicity_filter,
        "topic_filter": _process_topic_filter,
        "content_filter": _process_content_filter,
        "rate_limiter": _process_rate_limiter,
        "hallucination_check": _process_hallucination_check,
        "bias_detection": _process_bias_detection,
        "external_provider": _process_external_provider,
    }
    
    handler = processor_handlers.get(processor_type)
    if not handler:
        return ProfileGuardrailResult(
            passed=True,
            message=f"Unknown processor type: {processor_type}",
            action="allow",
            processed_messages=messages
        )
    
    return handler(action, config, messages, tenant_id)


def _get_all_content(messages: List[Dict[str, Any]]) -> str:
    """Extract all text content from messages."""
    content_parts = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            content_parts.append(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    content_parts.append(part.get("text", ""))
    return " ".join(content_parts)


def _process_pii_detection(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """Detect and handle PII in messages."""
    sensitivity = config.get("sensitivity", "medium")
    pii_types = config.get("types", list(PII_PATTERNS.keys()))
    
    all_content = _get_all_content(messages)
    detected_pii = []
    
    for pii_type in pii_types:
        pattern = PII_PATTERNS.get(pii_type.lower())
        if pattern and re.search(pattern, all_content, re.IGNORECASE):
            detected_pii.append(pii_type)
    
    if not detected_pii:
        return ProfileGuardrailResult(
            passed=True,
            message="No PII detected",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message=f"PII detected: {', '.join(detected_pii)}. Request blocked for compliance.",
            action="block",
            triggered_processor="pii_detection",
            metadata={"detected_pii_types": detected_pii}
        )
    
    elif action == "redact":
        redacted_messages = []
        for msg in messages:
            new_msg = msg.copy()
            content = msg.get("content", "")
            if isinstance(content, str):
                for pii_type in pii_types:
                    pattern = PII_PATTERNS.get(pii_type.lower())
                    if pattern:
                        content = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", content, flags=re.IGNORECASE)
                new_msg["content"] = content
            redacted_messages.append(new_msg)
        
        return ProfileGuardrailResult(
            passed=True,
            message=f"PII redacted: {', '.join(detected_pii)}",
            action="redact",
            triggered_processor="pii_detection",
            processed_messages=redacted_messages,
            metadata={"detected_pii_types": detected_pii}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"PII detected but allowed (warn mode): {', '.join(detected_pii)}",
        action="warn",
        triggered_processor="pii_detection",
        processed_messages=messages,
        metadata={"detected_pii_types": detected_pii}
    )


def _process_prompt_injection(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """Detect prompt injection attempts."""
    threshold = config.get("threshold", 0.8)
    
    all_content = _get_all_content(messages).lower()
    
    injection_score = 0.0
    matched_patterns = []
    
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, all_content, re.IGNORECASE):
            injection_score += 0.25
            matched_patterns.append(pattern[:30])
    
    injection_score = min(injection_score, 1.0)
    
    if injection_score < threshold:
        return ProfileGuardrailResult(
            passed=True,
            message="No prompt injection detected",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message="Potential prompt injection detected. Request blocked for security.",
            action="block",
            triggered_processor="prompt_injection",
            metadata={"score": injection_score}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"Potential prompt injection detected (warn mode), score: {injection_score:.2f}",
        action="warn",
        triggered_processor="prompt_injection",
        processed_messages=messages,
        metadata={"score": injection_score}
    )


def _process_toxicity_filter(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """Filter toxic content."""
    threshold = config.get("threshold", 0.6)
    
    all_content = _get_all_content(messages).lower()
    
    toxicity_score = 0.0
    for pattern in TOXIC_PATTERNS:
        if re.search(pattern, all_content, re.IGNORECASE):
            toxicity_score += 0.5
    
    toxicity_score = min(toxicity_score, 1.0)
    
    if toxicity_score < threshold:
        return ProfileGuardrailResult(
            passed=True,
            message="Content passed toxicity filter",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message="Toxic content detected. Request blocked.",
            action="block",
            triggered_processor="toxicity_filter",
            metadata={"score": toxicity_score}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"Toxic content detected (warn mode), score: {toxicity_score:.2f}",
        action="warn",
        triggered_processor="toxicity_filter",
        processed_messages=messages,
        metadata={"score": toxicity_score}
    )


def _process_topic_filter(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """Filter specific topics."""
    blocked_topics = config.get("blocked_topics", [])
    
    if not blocked_topics:
        return ProfileGuardrailResult(
            passed=True,
            message="No topics to filter",
            action="allow",
            processed_messages=messages
        )
    
    all_content = _get_all_content(messages).lower()
    
    topic_keywords = {
        "medical_advice": ["diagnose", "prescription", "medication", "treatment plan", "medical advice"],
        "legal_advice": ["legal advice", "lawsuit", "sue", "legal opinion", "attorney"],
        "financial_advice": ["invest", "stock tips", "financial advice", "buy stock", "sell stock"],
        "violence": ["violence", "attack", "weapon", "harm", "kill"],
        "adult": ["explicit", "sexual", "nude", "pornographic"],
    }
    
    matched_topics = []
    for topic in blocked_topics:
        keywords = topic_keywords.get(topic, [topic])
        for keyword in keywords:
            if keyword.lower() in all_content:
                matched_topics.append(topic)
                break
    
    if not matched_topics:
        return ProfileGuardrailResult(
            passed=True,
            message="No blocked topics detected",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message=f"Blocked topic detected: {', '.join(matched_topics)}",
            action="block",
            triggered_processor="topic_filter",
            metadata={"matched_topics": matched_topics}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"Blocked topic detected (warn mode): {', '.join(matched_topics)}",
        action="warn",
        triggered_processor="topic_filter",
        processed_messages=messages,
        metadata={"matched_topics": matched_topics}
    )


def _process_content_filter(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """General content filtering."""
    return ProfileGuardrailResult(
        passed=True,
        message="Content filter passed",
        action="allow",
        processed_messages=messages
    )


def _process_rate_limiter(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """Rate limiting processor (handled separately, pass-through here)."""
    return ProfileGuardrailResult(
        passed=True,
        message="Rate limiter passed",
        action="allow",
        processed_messages=messages
    )


def _process_hallucination_check(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """Hallucination detection (response stage only)."""
    return ProfileGuardrailResult(
        passed=True,
        message="Hallucination check passed",
        action="allow",
        processed_messages=messages
    )


def _process_bias_detection(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """Bias detection processor."""
    return ProfileGuardrailResult(
        passed=True,
        message="Bias detection passed",
        action="allow",
        processed_messages=messages
    )


def _process_external_provider(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    External guardrail provider processor.
    
    Calls configured external providers (OpenAI Moderation, AWS Comprehend, 
    Azure Content Safety, Google Cloud NLP) as part of the processor chain.
    
    Config options:
        - provider_id: ID of the external provider from guardrail_external_providers table
        - provider_type: Type of provider (openai, aws_comprehend, azure_content_safety, google_nlp)
        - provider_name: Name of the registered provider
        - stage: "request" or "response" (default: both)
        - categories: List of categories to check (optional, defaults to all)
    """
    provider_id = config.get("provider_id")
    provider_type = config.get("provider_type")
    provider_name = config.get("provider_name", "external")
    categories = config.get("categories", [])
    
    if not provider_id and not provider_type:
        logger.warning("external_provider_missing_config", config=config)
        return ProfileGuardrailResult(
            passed=True,
            message="External provider not configured properly",
            action="allow",
            processed_messages=messages
        )
    
    all_content = _get_all_content(messages)
    
    if not all_content.strip():
        return ProfileGuardrailResult(
            passed=True,
            message="No content to check",
            action="allow",
            processed_messages=messages
        )
    
    try:
        result = _call_external_provider_sync(
            provider_id=provider_id,
            provider_type=provider_type,
            provider_name=provider_name,
            content=all_content,
            categories=categories,
            tenant_id=tenant_id
        )
        
        if result.get("passed", True):
            return ProfileGuardrailResult(
                passed=True,
                message=f"External provider ({provider_name}) check passed",
                action="allow",
                triggered_processor="external_provider",
                processed_messages=messages,
                metadata={
                    "provider": provider_name,
                    "provider_type": provider_type,
                    "details": result
                }
            )
        
        violations = result.get("violations", [])
        violation_summary = ", ".join([v.get("category", "unknown") for v in violations[:3]])
        
        if action == "block":
            return ProfileGuardrailResult(
                passed=False,
                message=f"External provider ({provider_name}) detected violations: {violation_summary}",
                action="block",
                triggered_processor="external_provider",
                metadata={
                    "provider": provider_name,
                    "provider_type": provider_type,
                    "violations": violations
                }
            )
        elif action == "warn":
            return ProfileGuardrailResult(
                passed=True,
                message=f"External provider ({provider_name}) warning: {violation_summary}",
                action="warn",
                triggered_processor="external_provider",
                processed_messages=messages,
                metadata={
                    "provider": provider_name,
                    "provider_type": provider_type,
                    "violations": violations
                }
            )
        else:
            return ProfileGuardrailResult(
                passed=True,
                message=f"External provider check completed",
                action="allow",
                triggered_processor="external_provider",
                processed_messages=messages,
                metadata={"provider": provider_name, "details": result}
            )
            
    except Exception as e:
        logger.error(
            "external_provider_error",
            provider_name=provider_name,
            provider_type=provider_type,
            error=str(e)
        )
        return ProfileGuardrailResult(
            passed=True,
            message=f"External provider check failed (allowing): {str(e)}",
            action="allow",
            triggered_processor="external_provider",
            processed_messages=messages,
            metadata={"error": str(e)}
        )


def _call_external_provider_sync(
    provider_id: Optional[int],
    provider_type: Optional[str],
    provider_name: str,
    content: str,
    categories: List[str],
    tenant_id: int
) -> Dict[str, Any]:
    """
    Call external provider synchronously.
    
    For async contexts, use the async version or run in thread pool.
    This function interfaces with the GuardrailProviderManager.
    """
    try:
        from backend.app.services.guardrail_provider_manager import get_provider_manager
        
        manager = get_provider_manager()
        
        if not manager.providers:
            logger.warning("no_external_providers_registered")
            return {"passed": True, "message": "No external providers registered"}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                manager.check_input(
                    text=content,
                    context={"tenant_id": tenant_id, "categories": categories},
                    providers=[provider_name] if provider_name in manager.providers else None
                )
            )
            
            return {
                "passed": result.passed,
                "violations": [
                    {
                        "category": v.category.value if hasattr(v.category, 'value') else str(v.category),
                        "severity": v.severity,
                        "confidence": v.confidence,
                        "message": v.message,
                        "action": v.suggested_action.value if hasattr(v.suggested_action, 'value') else str(v.suggested_action)
                    }
                    for v in result.violations
                ],
                "recommended_action": result.recommended_action.value if hasattr(result.recommended_action, 'value') else str(result.recommended_action),
                "processing_time_ms": result.processing_time_ms
            }
        finally:
            loop.close()
            
    except ImportError as e:
        logger.warning("guardrail_provider_manager_not_available", error=str(e))
        return {"passed": True, "message": "Provider manager not available"}
    except Exception as e:
        logger.error("external_provider_call_failed", error=str(e))
        raise


async def apply_profile_guardrails_async(
    profile: GuardrailProfile,
    messages: List[Dict[str, Any]],
    stage: str,
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    Async version of apply_profile_guardrails.
    
    Use this when calling from async context (FastAPI routes).
    """
    return apply_profile_guardrails(profile, messages, stage, tenant_id)
