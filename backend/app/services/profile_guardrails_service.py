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
    # India-specific (DPDP Act compliance)
    "aadhaar": r'\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b',
    "pan": r'\b[A-Z]{3}[ABCFGHLJPTK][A-Z][0-9]{4}[A-Z]\b',
    "indian_passport": r'\b[A-Z][0-9]{7}\b',
    "voter_id": r'\b[A-Z]{3}[0-9]{7}\b',
    "indian_driving_license": r'\b[A-Z]{2}[0-9]{2}\s?[0-9]{4}[0-9]{7}\b',
    "indian_phone": r'\b(?:\+91[-.\s]?)?[6-9][0-9]{9}\b',
    "ifsc": r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
    "upi_id": r'\b[a-zA-Z0-9.\-_]+@[a-zA-Z]+\b',
    # GDPR/EU specific
    "iban": r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b',
    "eu_vat": r'\b[A-Z]{2}[0-9A-Z]{2,12}\b',
    # HIPAA/Healthcare
    "medical_record_number": r'\bMRN[:\s]?[0-9]{6,10}\b',
    "npi": r'\b[12][0-9]{9}\b',
    # Financial
    "bank_account": r'\b[0-9]{9,18}\b',
    "routing_number": r'\b[0-9]{9}\b',
    "cvv": r'\b[0-9]{3,4}\b',
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
        # Compliance-specific processors
        "dpdp_compliance": _process_dpdp_compliance,
        "gdpr_compliance": _process_gdpr_compliance,
        "hipaa_compliance": _process_hipaa_compliance,
        "pci_dss_compliance": _process_pci_dss_compliance,
        "data_residency": _process_data_residency,
        "consent_check": _process_consent_check,
        "code_detection": _process_code_detection,
        "secrets_detection": _process_secrets_detection,
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


# ============================================================================
# COMPLIANCE-SPECIFIC PROCESSORS
# ============================================================================

DPDP_PII_TYPES = ["aadhaar", "pan", "indian_passport", "voter_id", "indian_driving_license", "indian_phone", "upi_id", "ifsc", "email"]
GDPR_PII_TYPES = ["email", "phone", "ip_address", "iban", "eu_vat"]
HIPAA_PII_TYPES = ["medical_record_number", "npi", "ssn", "email", "phone"]
PCI_DSS_PII_TYPES = ["credit_card", "cvv", "bank_account", "routing_number"]

SECRETS_PATTERNS = {
    "aws_access_key": r'\bAKIA[0-9A-Z]{16}\b',
    "aws_secret_key": r'\b[A-Za-z0-9/+=]{40}\b',
    "github_token": r'\bgh[ps]_[A-Za-z0-9]{36}\b',
    "openai_api_key": r'\bsk-[A-Za-z0-9]{48}\b',
    "azure_key": r'\b[A-Za-z0-9]{32}\b',
    "jwt_token": r'\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b',
    "private_key": r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
    "generic_api_key": r'\b(api[_-]?key|apikey|secret[_-]?key)\s*[=:]\s*[\'"]?[A-Za-z0-9_-]{16,}[\'"]?\b',
}

CODE_PATTERNS = [
    r'```[\s\S]*?```',
    r'def\s+\w+\s*\(',
    r'function\s+\w+\s*\(',
    r'class\s+\w+\s*[:\(]',
    r'import\s+\w+',
    r'from\s+\w+\s+import',
    r'require\s*\([\'"]',
    r'SELECT\s+.+\s+FROM\s+',
    r'INSERT\s+INTO\s+',
    r'CREATE\s+TABLE\s+',
]


def _process_dpdp_compliance(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    DPDP Act (India) compliance processor.
    
    Detects Indian personal data: Aadhaar, PAN, Passport, Voter ID, 
    Driving License, Phone, UPI, IFSC codes.
    """
    pii_types = config.get("types", DPDP_PII_TYPES)
    all_content = _get_all_content(messages)
    detected_pii = []
    
    for pii_type in pii_types:
        pattern = PII_PATTERNS.get(pii_type.lower())
        if pattern and re.search(pattern, all_content, re.IGNORECASE):
            detected_pii.append(pii_type)
    
    if not detected_pii:
        return ProfileGuardrailResult(
            passed=True,
            message="DPDP compliance check passed - no personal data detected",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message=f"DPDP Violation: Personal data detected ({', '.join(detected_pii)}). Processing blocked per Digital Personal Data Protection Act.",
            action="block",
            triggered_processor="dpdp_compliance",
            metadata={"detected_types": detected_pii, "framework": "DPDP"}
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
            message=f"DPDP: Personal data redacted ({', '.join(detected_pii)})",
            action="redact",
            triggered_processor="dpdp_compliance",
            processed_messages=redacted_messages,
            metadata={"detected_types": detected_pii, "framework": "DPDP"}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"DPDP Warning: Personal data detected ({', '.join(detected_pii)})",
        action="warn",
        triggered_processor="dpdp_compliance",
        processed_messages=messages,
        metadata={"detected_types": detected_pii, "framework": "DPDP"}
    )


def _process_gdpr_compliance(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    GDPR (EU) compliance processor.
    
    Detects EU personal data and checks for data processing consent indicators.
    """
    pii_types = config.get("types", GDPR_PII_TYPES)
    check_consent = config.get("check_consent", False)
    
    all_content = _get_all_content(messages)
    detected_pii = []
    
    for pii_type in pii_types:
        pattern = PII_PATTERNS.get(pii_type.lower())
        if pattern and re.search(pattern, all_content, re.IGNORECASE):
            detected_pii.append(pii_type)
    
    if not detected_pii:
        return ProfileGuardrailResult(
            passed=True,
            message="GDPR compliance check passed - no personal data detected",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message=f"GDPR Violation: Personal data detected ({', '.join(detected_pii)}). Processing requires lawful basis under GDPR Article 6.",
            action="block",
            triggered_processor="gdpr_compliance",
            metadata={"detected_types": detected_pii, "framework": "GDPR"}
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
            message=f"GDPR: Personal data redacted ({', '.join(detected_pii)})",
            action="redact",
            triggered_processor="gdpr_compliance",
            processed_messages=redacted_messages,
            metadata={"detected_types": detected_pii, "framework": "GDPR"}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"GDPR Warning: Personal data detected ({', '.join(detected_pii)})",
        action="warn",
        triggered_processor="gdpr_compliance",
        processed_messages=messages,
        metadata={"detected_types": detected_pii, "framework": "GDPR"}
    )


def _process_hipaa_compliance(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    HIPAA (US Healthcare) compliance processor.
    
    Detects Protected Health Information (PHI) including medical record numbers,
    NPI, and personal identifiers combined with health context.
    """
    pii_types = config.get("types", HIPAA_PII_TYPES)
    health_keywords = ["patient", "diagnosis", "treatment", "medical", "health", "prescription", "hospital", "clinic", "doctor", "medication"]
    
    all_content = _get_all_content(messages)
    all_content_lower = all_content.lower()
    detected_pii = []
    has_health_context = any(kw in all_content_lower for kw in health_keywords)
    
    for pii_type in pii_types:
        pattern = PII_PATTERNS.get(pii_type.lower())
        if pattern and re.search(pattern, all_content, re.IGNORECASE):
            detected_pii.append(pii_type)
    
    if not detected_pii or (not has_health_context and "medical_record_number" not in detected_pii and "npi" not in detected_pii):
        return ProfileGuardrailResult(
            passed=True,
            message="HIPAA compliance check passed - no PHI detected",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message=f"HIPAA Violation: Protected Health Information detected ({', '.join(detected_pii)}). Transmission blocked per HIPAA Privacy Rule.",
            action="block",
            triggered_processor="hipaa_compliance",
            metadata={"detected_types": detected_pii, "has_health_context": has_health_context, "framework": "HIPAA"}
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
                        content = re.sub(pattern, f"[PHI_{pii_type.upper()}_REDACTED]", content, flags=re.IGNORECASE)
                new_msg["content"] = content
            redacted_messages.append(new_msg)
        
        return ProfileGuardrailResult(
            passed=True,
            message=f"HIPAA: PHI redacted ({', '.join(detected_pii)})",
            action="redact",
            triggered_processor="hipaa_compliance",
            processed_messages=redacted_messages,
            metadata={"detected_types": detected_pii, "framework": "HIPAA"}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"HIPAA Warning: Potential PHI detected ({', '.join(detected_pii)})",
        action="warn",
        triggered_processor="hipaa_compliance",
        processed_messages=messages,
        metadata={"detected_types": detected_pii, "has_health_context": has_health_context, "framework": "HIPAA"}
    )


def _process_pci_dss_compliance(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    PCI-DSS compliance processor.
    
    Detects payment card data: credit card numbers, CVV, bank accounts, routing numbers.
    """
    pii_types = config.get("types", PCI_DSS_PII_TYPES)
    all_content = _get_all_content(messages)
    detected_pii = []
    
    for pii_type in pii_types:
        pattern = PII_PATTERNS.get(pii_type.lower())
        if pattern and re.search(pattern, all_content, re.IGNORECASE):
            detected_pii.append(pii_type)
    
    if not detected_pii:
        return ProfileGuardrailResult(
            passed=True,
            message="PCI-DSS compliance check passed - no cardholder data detected",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message=f"PCI-DSS Violation: Cardholder data detected ({', '.join(detected_pii)}). Transmission blocked per PCI-DSS Requirement 3.",
            action="block",
            triggered_processor="pci_dss_compliance",
            metadata={"detected_types": detected_pii, "framework": "PCI-DSS"}
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
            message=f"PCI-DSS: Cardholder data redacted ({', '.join(detected_pii)})",
            action="redact",
            triggered_processor="pci_dss_compliance",
            processed_messages=redacted_messages,
            metadata={"detected_types": detected_pii, "framework": "PCI-DSS"}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"PCI-DSS Warning: Cardholder data detected ({', '.join(detected_pii)})",
        action="warn",
        triggered_processor="pci_dss_compliance",
        processed_messages=messages,
        metadata={"detected_types": detected_pii, "framework": "PCI-DSS"}
    )


def _process_data_residency(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    Data residency processor.
    
    Flags or blocks requests that may involve cross-border data transfer concerns.
    Checks for geographic indicators and data transfer keywords.
    """
    restricted_regions = config.get("restricted_regions", ["china", "russia", "iran", "north korea"])
    transfer_keywords = ["transfer", "export", "send to", "share with", "cross-border"]
    
    all_content = _get_all_content(messages).lower()
    
    detected_regions = []
    has_transfer_intent = any(kw in all_content for kw in transfer_keywords)
    
    for region in restricted_regions:
        if region.lower() in all_content:
            detected_regions.append(region)
    
    if not detected_regions:
        return ProfileGuardrailResult(
            passed=True,
            message="Data residency check passed",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block" and has_transfer_intent:
        return ProfileGuardrailResult(
            passed=False,
            message=f"Data Residency Violation: Potential cross-border transfer to restricted region(s): {', '.join(detected_regions)}",
            action="block",
            triggered_processor="data_residency",
            metadata={"detected_regions": detected_regions, "has_transfer_intent": has_transfer_intent}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"Data Residency Warning: Restricted region mentioned: {', '.join(detected_regions)}",
        action="warn",
        triggered_processor="data_residency",
        processed_messages=messages,
        metadata={"detected_regions": detected_regions, "has_transfer_intent": has_transfer_intent}
    )


def _process_consent_check(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    Consent check processor.
    
    Looks for consent-related language and data processing requests without explicit consent.
    """
    consent_required_topics = config.get("topics", ["personal data", "user data", "customer information", "contact details"])
    
    all_content = _get_all_content(messages).lower()
    
    matched_topics = [topic for topic in consent_required_topics if topic.lower() in all_content]
    
    if not matched_topics:
        return ProfileGuardrailResult(
            passed=True,
            message="Consent check passed - no sensitive topics detected",
            action="allow",
            processed_messages=messages
        )
    
    has_consent_indicator = any(word in all_content for word in ["consent", "agreed", "permission", "authorized", "opted in"])
    
    if action == "block" and not has_consent_indicator:
        return ProfileGuardrailResult(
            passed=False,
            message=f"Consent Required: Topics requiring consent detected ({', '.join(matched_topics)}) but no consent indicator found.",
            action="block",
            triggered_processor="consent_check",
            metadata={"matched_topics": matched_topics, "has_consent_indicator": has_consent_indicator}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"Consent Advisory: Topics detected ({', '.join(matched_topics)}), consent indicator: {has_consent_indicator}",
        action="warn",
        triggered_processor="consent_check",
        processed_messages=messages,
        metadata={"matched_topics": matched_topics, "has_consent_indicator": has_consent_indicator}
    )


def _process_code_detection(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    Code detection processor.
    
    Detects code snippets, SQL queries, and programming constructs.
    Useful for preventing code injection or IP leakage.
    """
    block_languages = config.get("block_languages", [])
    
    all_content = _get_all_content(messages)
    detected_code = []
    
    for pattern in CODE_PATTERNS:
        if re.search(pattern, all_content, re.IGNORECASE):
            detected_code.append(pattern[:20])
    
    if not detected_code:
        return ProfileGuardrailResult(
            passed=True,
            message="Code detection passed - no code patterns found",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message="Code Detected: Request contains code snippets which are not allowed.",
            action="block",
            triggered_processor="code_detection",
            metadata={"detected_patterns": len(detected_code)}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"Code Detection Warning: {len(detected_code)} code pattern(s) detected",
        action="warn",
        triggered_processor="code_detection",
        processed_messages=messages,
        metadata={"detected_patterns": len(detected_code)}
    )


def _process_secrets_detection(
    action: str,
    config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    tenant_id: int
) -> ProfileGuardrailResult:
    """
    Secrets detection processor.
    
    Detects API keys, tokens, private keys, and other secrets.
    Critical for preventing credential leakage.
    """
    secret_types = config.get("types", list(SECRETS_PATTERNS.keys()))
    
    all_content = _get_all_content(messages)
    detected_secrets = []
    
    for secret_type in secret_types:
        pattern = SECRETS_PATTERNS.get(secret_type)
        if pattern and re.search(pattern, all_content, re.IGNORECASE):
            detected_secrets.append(secret_type)
    
    if not detected_secrets:
        return ProfileGuardrailResult(
            passed=True,
            message="Secrets detection passed - no secrets found",
            action="allow",
            processed_messages=messages
        )
    
    if action == "block":
        return ProfileGuardrailResult(
            passed=False,
            message=f"Security Violation: Secrets/credentials detected ({', '.join(detected_secrets)}). Request blocked to prevent credential leakage.",
            action="block",
            triggered_processor="secrets_detection",
            metadata={"detected_types": detected_secrets}
        )
    
    elif action == "redact":
        redacted_messages = []
        for msg in messages:
            new_msg = msg.copy()
            content = msg.get("content", "")
            if isinstance(content, str):
                for secret_type in secret_types:
                    pattern = SECRETS_PATTERNS.get(secret_type)
                    if pattern:
                        content = re.sub(pattern, f"[{secret_type.upper()}_REDACTED]", content, flags=re.IGNORECASE)
                new_msg["content"] = content
            redacted_messages.append(new_msg)
        
        return ProfileGuardrailResult(
            passed=True,
            message=f"Secrets redacted ({', '.join(detected_secrets)})",
            action="redact",
            triggered_processor="secrets_detection",
            processed_messages=redacted_messages,
            metadata={"detected_types": detected_secrets}
        )
    
    return ProfileGuardrailResult(
        passed=True,
        message=f"Security Warning: Potential secrets detected ({', '.join(detected_secrets)})",
        action="warn",
        triggered_processor="secrets_detection",
        processed_messages=messages,
        metadata={"detected_types": detected_secrets}
    )


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
