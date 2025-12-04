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


class GoogleCloudNLPProvider(BaseGuardrailProvider):
    """
    Google Cloud Natural Language API guardrail provider.
    
    Supports: Sentiment analysis, content classification, entity recognition
    API: https://cloud.google.com/natural-language/docs
    """
    
    NLP_ENDPOINT = "https://language.googleapis.com/v1/documents"
    
    def __init__(self, config: GuardrailProviderConfig):
        super().__init__(config)
        
        self.api_key = config.api_key
        if not self.api_key:
            raise ValueError("Google Cloud API key is required")
        
        self.sentiment_enabled = config.custom_config.get("sentiment_analysis", True)
        self.classification_enabled = config.custom_config.get("content_classification", True)
        self.entity_recognition_enabled = config.custom_config.get("entity_recognition", False)
    
    async def check_input(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Check input text using Google Cloud NLP."""
        return await self._analyze(text, "input", context)
    
    async def check_output(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Check output text using Google Cloud NLP."""
        return await self._analyze(text, "output", context)
    
    async def _analyze(
        self,
        text: str,
        stage: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Perform Google Cloud NLP analysis."""
        start_time = time.time()
        violations = []
        
        try:
            # Sentiment Analysis
            if self.sentiment_enabled:
                sentiment_violations = await self._analyze_sentiment(text)
                violations.extend(sentiment_violations)
            
            # Content Classification
            if self.classification_enabled:
                classification_violations = await self._classify_content(text)
                violations.extend(classification_violations)
            
            processing_time = (time.time() - start_time) * 1000
            
            recommended_action = GuardrailAction.ALLOW
            if any(v.suggested_action == GuardrailAction.BLOCK for v in violations):
                recommended_action = GuardrailAction.BLOCK
            elif violations:
                recommended_action = GuardrailAction.WARN
            
            return GuardrailResult(
                provider="Google Cloud NLP",
                passed=len(violations) == 0 or recommended_action != GuardrailAction.BLOCK,
                violations=violations,
                recommended_action=recommended_action,
                processing_time_ms=processing_time,
                metadata={"stage": stage}
            )
        
        except Exception as e:
            logger.error(
                "google_nlp_error",
                error=str(e),
                text_length=len(text)
            )
            processing_time = (time.time() - start_time) * 1000
            return GuardrailResult(
                provider="Google Cloud NLP",
                passed=True,
                violations=[],
                recommended_action=GuardrailAction.ALLOW,
                processing_time_ms=processing_time,
                metadata={"error": str(e), "failed_gracefully": True}
            )
    
    async def _analyze_sentiment(self, text: str) -> List[GuardrailViolation]:
        """Analyze sentiment."""
        violations = []
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(
                    f"{self.NLP_ENDPOINT}:analyzeSentiment",
                    params={"key": self.api_key},
                    json={
                        "document": {
                            "type": "PLAIN_TEXT",
                            "content": text
                        },
                        "encodingType": "UTF8"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    sentiment = data.get("documentSentiment", {})
                    score = sentiment.get("score", 0.0)  # -1 to 1
                    magnitude = sentiment.get("magnitude", 0.0)
                    
                    # Flag very negative sentiment
                    if score < -0.5 and magnitude > 2.0:
                        violations.append(GuardrailViolation(
                            category=GuardrailCategory.SENTIMENT,
                            severity=abs(score),
                            confidence=0.85,
                            message=f"Highly negative sentiment detected (score: {score:.2f})",
                            details={
                                "score": score,
                                "magnitude": magnitude
                            },
                            suggested_action=GuardrailAction.WARN
                        ))
        
        except Exception as e:
            logger.error("google_sentiment_error", error=str(e))
        
        return violations
    
    async def _classify_content(self, text: str) -> List[GuardrailViolation]:
        """Classify content."""
        violations = []
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(
                    f"{self.NLP_ENDPOINT}:classifyText",
                    params={"key": self.api_key},
                    json={
                        "document": {
                            "type": "PLAIN_TEXT",
                            "content": text
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    categories = data.get("categories", [])
                    
                    # Flag sensitive categories
                    sensitive_categories = [
                        "/Adult", "/Sensitive Subjects", 
                        "/Law & Government/Legal", "/Health/Medical"
                    ]
                    
                    for category in categories:
                        name = category.get("name", "")
                        confidence = category.get("confidence", 0.0)
                        
                        if any(sens in name for sens in sensitive_categories) and confidence > 0.7:
                            violations.append(GuardrailViolation(
                                category=GuardrailCategory.CUSTOM,
                                severity=confidence,
                                confidence=confidence,
                                message=f"Sensitive content category: {name}",
                                details={"category": name},
                                suggested_action=GuardrailAction.WARN
                            ))
        
        except Exception as e:
            logger.error("google_classification_error", error=str(e))
        
        return violations
    
    def get_capabilities(self) -> List[GuardrailCategory]:
        """Get supported categories."""
        capabilities = [GuardrailCategory.SENTIMENT]
        if self.classification_enabled:
            capabilities.append(GuardrailCategory.CUSTOM)
        return capabilities
    
    async def health_check(self) -> bool:
        """Check if Google Cloud NLP is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    f"{self.NLP_ENDPOINT}:analyzeSentiment",
                    params={"key": self.api_key},
                    json={
                        "document": {
                            "type": "PLAIN_TEXT",
                            "content": "test"
                        }
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.error("google_health_check_failed", error=str(e))
            return False
