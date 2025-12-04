from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum


class GuardrailAction(str, Enum):
    """Action to take when guardrail is triggered."""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    REDACT = "redact"


class GuardrailCategory(str, Enum):
    """Categories of guardrail checks."""
    PII = "pii"
    TOXICITY = "toxicity"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SEXUAL_CONTENT = "sexual"
    SELF_HARM = "self_harm"
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    FINANCIAL_ADVICE = "financial_advice"
    SENTIMENT = "sentiment"
    LANGUAGE = "language"
    CUSTOM = "custom"


class GuardrailViolation(BaseModel):
    """Details of a guardrail violation."""
    category: GuardrailCategory
    severity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    message: str
    details: Dict[str, Any] = {}
    suggested_action: GuardrailAction = GuardrailAction.WARN


class GuardrailResult(BaseModel):
    """Result of guardrail check."""
    provider: str
    passed: bool
    violations: List[GuardrailViolation] = []
    recommended_action: GuardrailAction = GuardrailAction.ALLOW
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = {}
    
    @property
    def is_blocked(self) -> bool:
        """Check if any violation recommends blocking."""
        return any(
            v.suggested_action == GuardrailAction.BLOCK
            for v in self.violations
        )
    
    @property
    def highest_severity(self) -> float:
        """Get highest severity across all violations."""
        if not self.violations:
            return 0.0
        return max(v.severity for v in self.violations)


class GuardrailProviderConfig(BaseModel):
    """Configuration for a guardrail provider."""
    enabled: bool = True
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    region: Optional[str] = None
    timeout_seconds: int = 10
    retry_attempts: int = 2
    
    # Category-specific thresholds
    thresholds: Dict[str, float] = {
        "toxicity": 0.7,
        "hate_speech": 0.7,
        "violence": 0.7,
        "sexual": 0.7,
        "self_harm": 0.7
    }
    
    # Custom configuration
    custom_config: Dict[str, Any] = {}


class BaseGuardrailProvider(ABC):
    """Abstract base class for guardrail providers."""
    
    def __init__(self, config: GuardrailProviderConfig):
        self.config = config
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    async def check_input(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Check input text for violations.
        
        Args:
            text: The input text to check
            context: Additional context (user_id, conversation history, etc.)
        
        Returns:
            GuardrailResult with violations and recommendations
        """
        pass
    
    @abstractmethod
    async def check_output(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Check output text for violations.
        
        Args:
            text: The output text to check
            context: Additional context (prompt, model, etc.)
        
        Returns:
            GuardrailResult with violations and recommendations
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[GuardrailCategory]:
        """
        Get list of guardrail categories this provider supports.
        
        Returns:
            List of supported GuardrailCategory values
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if provider is healthy and accessible.
        
        Returns:
            True if provider is healthy, False otherwise
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata."""
        return {
            "name": self.provider_name,
            "enabled": self.config.enabled,
            "capabilities": [c.value for c in self.get_capabilities()],
            "thresholds": self.config.thresholds
        }
    
    def _should_block(self, severity: float, category: str) -> bool:
        """Determine if severity exceeds threshold for category."""
        threshold = self.config.thresholds.get(category, 0.7)
        return severity >= threshold
