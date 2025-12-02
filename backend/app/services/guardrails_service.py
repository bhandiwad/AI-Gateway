import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import structlog

logger = structlog.get_logger()


class GuardrailAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REDACT = "redact"
    WARN = "warn"


class GuardrailResult:
    def __init__(
        self,
        passed: bool,
        action: GuardrailAction,
        triggered_rule: Optional[str] = None,
        modified_content: Optional[str] = None,
        message: Optional[str] = None
    ):
        self.passed = passed
        self.action = action
        self.triggered_rule = triggered_rule
        self.modified_content = modified_content
        self.message = message


PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
    "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
}

TOXIC_PATTERNS = [
    r'\b(kill|murder|attack|bomb|terror|hack|steal|illegal|drug)\b',
]

PROMPT_INJECTION_PATTERNS = [
    r'ignore\s+(previous|all)\s+(instructions?|prompts?)',
    r'forget\s+(everything|all|previous)',
    r'you\s+are\s+now\s+(?:a\s+)?(?:new|different)',
    r'pretend\s+(?:to\s+be|you\s+are)',
    r'act\s+as\s+(?:if\s+)?(?:you\s+(?:are|were))?',
    r'disregard\s+(?:all|previous|your)',
    r'override\s+(?:your|all|previous)',
    r'\[system\]',
    r'jailbreak',
]


class GuardrailsService:
    def __init__(self):
        self.pii_patterns = {k: re.compile(v, re.IGNORECASE) for k, v in PII_PATTERNS.items()}
        self.toxic_patterns = [re.compile(p, re.IGNORECASE) for p in TOXIC_PATTERNS]
        self.injection_patterns = [re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS]
    
    def check_pii(self, text: str, redact: bool = True) -> Tuple[bool, str, List[str]]:
        found_pii = []
        modified_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            if matches:
                found_pii.extend([(pii_type, m) for m in matches])
                if redact:
                    modified_text = pattern.sub(f"[REDACTED_{pii_type.upper()}]", modified_text)
        
        has_pii = len(found_pii) > 0
        return has_pii, modified_text, [f[0] for f in found_pii]
    
    def check_toxicity(self, text: str) -> Tuple[bool, List[str]]:
        found_toxic = []
        
        for pattern in self.toxic_patterns:
            matches = pattern.findall(text)
            if matches:
                found_toxic.extend(matches)
        
        return len(found_toxic) > 0, found_toxic
    
    def check_prompt_injection(self, text: str) -> Tuple[bool, List[str]]:
        found_injections = []
        
        for pattern in self.injection_patterns:
            matches = pattern.findall(text)
            if matches:
                found_injections.extend([str(m) for m in matches])
        
        return len(found_injections) > 0, found_injections
    
    def validate_input(
        self,
        content: str,
        tenant_id: int,
        policies: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        policies = policies or {}
        
        has_injection, injection_matches = self.check_prompt_injection(content)
        if has_injection and policies.get("block_prompt_injection", True):
            logger.warning(
                "prompt_injection_detected",
                tenant_id=tenant_id,
                matches=injection_matches
            )
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                triggered_rule="prompt_injection",
                message="Potential prompt injection detected. Request blocked."
            )
        
        has_pii, redacted_content, pii_types = self.check_pii(content)
        if has_pii:
            action = policies.get("pii_action", "redact")
            if action == "block":
                return GuardrailResult(
                    passed=False,
                    action=GuardrailAction.BLOCK,
                    triggered_rule="pii_detection",
                    message=f"PII detected ({', '.join(pii_types)}). Request blocked."
                )
            elif action == "redact":
                return GuardrailResult(
                    passed=True,
                    action=GuardrailAction.REDACT,
                    triggered_rule="pii_detection",
                    modified_content=redacted_content,
                    message=f"PII detected and redacted ({', '.join(pii_types)})."
                )
        
        has_toxic, toxic_matches = self.check_toxicity(content)
        if has_toxic and policies.get("block_toxic", False):
            return GuardrailResult(
                passed=False,
                action=GuardrailAction.BLOCK,
                triggered_rule="toxicity",
                message="Potentially harmful content detected. Request blocked."
            )
        
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.ALLOW
        )
    
    def validate_output(
        self,
        content: str,
        tenant_id: int,
        policies: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        policies = policies or {}
        
        has_pii, redacted_content, pii_types = self.check_pii(content)
        if has_pii:
            action = policies.get("output_pii_action", "redact")
            if action == "block":
                return GuardrailResult(
                    passed=False,
                    action=GuardrailAction.BLOCK,
                    triggered_rule="output_pii",
                    message=f"PII detected in response ({', '.join(pii_types)}). Response blocked."
                )
            elif action == "redact":
                return GuardrailResult(
                    passed=True,
                    action=GuardrailAction.REDACT,
                    triggered_rule="output_pii",
                    modified_content=redacted_content,
                    message=f"PII redacted from response ({', '.join(pii_types)})."
                )
        
        return GuardrailResult(
            passed=True,
            action=GuardrailAction.ALLOW
        )
    
    def validate_request(
        self,
        messages: List[Dict[str, Any]],
        tenant_id: int,
        policies: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        for msg in messages:
            content = msg.get("content", "")
            if content:
                result = self.validate_input(content, tenant_id, policies)
                if not result.passed:
                    return result
                if result.action == GuardrailAction.REDACT and result.modified_content:
                    msg["content"] = result.modified_content
        
        return GuardrailResult(passed=True, action=GuardrailAction.ALLOW)


guardrails_service = GuardrailsService()
