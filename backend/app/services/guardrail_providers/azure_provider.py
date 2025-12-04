import time
import httpx
from typing import List, Dict, Any, Optional
import structlog

from backend.app.services.guardrail_providers.base import (
    BaseGuardrailProvider,
    GuardrailResult,
    GuardrailViolation,
    GuardrailCategory,
    GuardrailAction,
    GuardrailProviderConfig
)

logger = structlog.get_logger()


class AzureContentSafetyProvider(BaseGuardrailProvider):
    """
    Azure Content Safety API guardrail provider.
    
    Supports: Hate speech, violence, self-harm, sexual content detection
    API: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/
    """
    
    def __init__(self, config: GuardrailProviderConfig):
        super().__init__(config)
        
        self.api_key = config.api_key
        self.endpoint = config.api_endpoint or "https://your-resource.cognitiveservices.azure.com"
        
        if not self.api_key:
            raise ValueError("Azure API key is required")
        
        self.api_version = config.custom_config.get("api_version", "2023-10-01")
    
    async def check_input(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Check input text using Azure Content Safety."""
        return await self._analyze(text, "input", context)
    
    async def check_output(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Check output text using Azure Content Safety."""
        return await self._analyze(text, "output", context)
    
    async def _analyze(
        self,
        text: str,
        stage: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Perform Azure Content Safety analysis."""
        start_time = time.time()
        violations = []
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(
                    f"{self.endpoint}/contentsafety/text:analyze",
                    params={"api-version": self.api_version},
                    headers={
                        "Ocp-Apim-Subscription-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": text,
                        "categories": ["Hate", "SelfHarm", "Sexual", "Violence"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Map Azure categories to our categories
                    category_mapping = {
                        "Hate": GuardrailCategory.HATE_SPEECH,
                        "SelfHarm": GuardrailCategory.SELF_HARM,
                        "Sexual": GuardrailCategory.SEXUAL_CONTENT,
                        "Violence": GuardrailCategory.VIOLENCE
                    }
                    
                    # Azure returns severity levels 0-6 (0=safe, 6=severe)
                    for azure_category, our_category in category_mapping.items():
                        category_result = data.get(f"{azure_category.lower()}Result", {})
                        severity_level = category_result.get("severity", 0)
                        
                        if severity_level > 0:
                            # Convert 0-6 scale to 0-1
                            normalized_severity = severity_level / 6.0
                            
                            suggested_action = GuardrailAction.WARN
                            if severity_level >= 4:
                                suggested_action = GuardrailAction.BLOCK
                            elif severity_level >= 2:
                                suggested_action = GuardrailAction.WARN
                            else:
                                suggested_action = GuardrailAction.ALLOW
                            
                            if severity_level >= 2:  # Only report moderate+ violations
                                violations.append(GuardrailViolation(
                                    category=our_category,
                                    severity=normalized_severity,
                                    confidence=0.90,
                                    message=f"{azure_category} content detected (severity: {severity_level}/6)",
                                    details={
                                        "azure_category": azure_category,
                                        "severity_level": severity_level
                                    },
                                    suggested_action=suggested_action
                                ))
            
            processing_time = (time.time() - start_time) * 1000
            
            recommended_action = GuardrailAction.ALLOW
            if any(v.suggested_action == GuardrailAction.BLOCK for v in violations):
                recommended_action = GuardrailAction.BLOCK
            elif violations:
                recommended_action = GuardrailAction.WARN
            
            return GuardrailResult(
                provider="Azure Content Safety",
                passed=len(violations) == 0 or recommended_action != GuardrailAction.BLOCK,
                violations=violations,
                recommended_action=recommended_action,
                processing_time_ms=processing_time,
                metadata={"stage": stage}
            )
        
        except httpx.HTTPError as e:
            logger.error(
                "azure_content_safety_error",
                error=str(e),
                text_length=len(text)
            )
            processing_time = (time.time() - start_time) * 1000
            return GuardrailResult(
                provider="Azure Content Safety",
                passed=True,
                violations=[],
                recommended_action=GuardrailAction.ALLOW,
                processing_time_ms=processing_time,
                metadata={"error": str(e), "failed_gracefully": True}
            )
    
    def get_capabilities(self) -> List[GuardrailCategory]:
        """Get supported categories."""
        return [
            GuardrailCategory.HATE_SPEECH,
            GuardrailCategory.SELF_HARM,
            GuardrailCategory.SEXUAL_CONTENT,
            GuardrailCategory.VIOLENCE
        ]
    
    async def health_check(self) -> bool:
        """Check if Azure Content Safety is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    f"{self.endpoint}/contentsafety/text:analyze",
                    params={"api-version": self.api_version},
                    headers={
                        "Ocp-Apim-Subscription-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": "test",
                        "categories": ["Hate"]
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.error("azure_health_check_failed", error=str(e))
            return False
