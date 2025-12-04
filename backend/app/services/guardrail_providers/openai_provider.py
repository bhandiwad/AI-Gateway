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


class OpenAIGuardrailProvider(BaseGuardrailProvider):
    """
    OpenAI Moderation API guardrail provider.
    
    Supports: toxicity, hate speech, self-harm, sexual content, violence
    API: https://platform.openai.com/docs/api-reference/moderations
    """
    
    MODERATION_ENDPOINT = "https://api.openai.com/v1/moderations"
    
    # Map OpenAI categories to our GuardrailCategory
    CATEGORY_MAPPING = {
        "hate": GuardrailCategory.HATE_SPEECH,
        "hate/threatening": GuardrailCategory.HATE_SPEECH,
        "harassment": GuardrailCategory.TOXICITY,
        "harassment/threatening": GuardrailCategory.TOXICITY,
        "self-harm": GuardrailCategory.SELF_HARM,
        "self-harm/intent": GuardrailCategory.SELF_HARM,
        "self-harm/instructions": GuardrailCategory.SELF_HARM,
        "sexual": GuardrailCategory.SEXUAL_CONTENT,
        "sexual/minors": GuardrailCategory.SEXUAL_CONTENT,
        "violence": GuardrailCategory.VIOLENCE,
        "violence/graphic": GuardrailCategory.VIOLENCE,
    }
    
    def __init__(self, config: GuardrailProviderConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("OpenAI API key is required")
        self.api_key = config.api_key
        self.model = config.custom_config.get("model", "text-moderation-latest")
    
    async def check_input(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Check input text using OpenAI Moderation API."""
        return await self._moderate(text, "input", context)
    
    async def check_output(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Check output text using OpenAI Moderation API."""
        return await self._moderate(text, "output", context)
    
    async def _moderate(
        self,
        text: str,
        stage: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Perform moderation check."""
        start_time = time.time()
        violations = []
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(
                    self.MODERATION_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": text,
                        "model": self.model
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse results
            if data.get("results"):
                result = data["results"][0]
                categories = result.get("categories", {})
                category_scores = result.get("category_scores", {})
                
                for category_key, flagged in categories.items():
                    score = category_scores.get(category_key, 0.0)
                    
                    # Map to our category
                    our_category = self.CATEGORY_MAPPING.get(
                        category_key,
                        GuardrailCategory.CUSTOM
                    )
                    
                    # Only add violations if flagged or score is high
                    if flagged or score >= 0.5:
                        severity = score
                        suggested_action = GuardrailAction.BLOCK if flagged else GuardrailAction.WARN
                        
                        violations.append(GuardrailViolation(
                            category=our_category,
                            severity=severity,
                            confidence=0.95,  # OpenAI is generally confident
                            message=f"{category_key} content detected",
                            details={
                                "openai_category": category_key,
                                "score": score,
                                "flagged": flagged
                            },
                            suggested_action=suggested_action
                        ))
            
            processing_time = (time.time() - start_time) * 1000
            
            # Determine overall recommendation
            recommended_action = GuardrailAction.ALLOW
            if any(v.suggested_action == GuardrailAction.BLOCK for v in violations):
                recommended_action = GuardrailAction.BLOCK
            elif violations:
                recommended_action = GuardrailAction.WARN
            
            return GuardrailResult(
                provider="OpenAI Moderation",
                passed=len(violations) == 0 or recommended_action != GuardrailAction.BLOCK,
                violations=violations,
                recommended_action=recommended_action,
                processing_time_ms=processing_time,
                metadata={
                    "model": self.model,
                    "stage": stage
                }
            )
        
        except httpx.HTTPError as e:
            logger.error(
                "openai_moderation_error",
                error=str(e),
                text_length=len(text)
            )
            processing_time = (time.time() - start_time) * 1000
            return GuardrailResult(
                provider="OpenAI Moderation",
                passed=True,  # Fail open by default
                violations=[],
                recommended_action=GuardrailAction.ALLOW,
                processing_time_ms=processing_time,
                metadata={
                    "error": str(e),
                    "failed_gracefully": True
                }
            )
    
    def get_capabilities(self) -> List[GuardrailCategory]:
        """Get supported categories."""
        return [
            GuardrailCategory.HATE_SPEECH,
            GuardrailCategory.TOXICITY,
            GuardrailCategory.SELF_HARM,
            GuardrailCategory.SEXUAL_CONTENT,
            GuardrailCategory.VIOLENCE
        ]
    
    async def health_check(self) -> bool:
        """Check if OpenAI Moderation API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    self.MODERATION_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": "test"
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.error("openai_health_check_failed", error=str(e))
            return False
