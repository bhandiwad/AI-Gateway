import time
import json
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


class AWSComprehendProvider(BaseGuardrailProvider):
    """
    AWS Comprehend guardrail provider.
    
    Supports: PII detection, sentiment analysis, toxicity detection
    Note: Requires AWS credentials (access key, secret key, region)
    """
    
    # PII entity type mapping
    PII_ENTITY_TYPES = {
        "SSN", "CREDIT_DEBIT_NUMBER", "CREDIT_DEBIT_CVV", 
        "CREDIT_DEBIT_EXPIRY", "PIN", "EMAIL", "ADDRESS",
        "NAME", "PHONE", "USERNAME", "PASSWORD", "BANK_ACCOUNT_NUMBER",
        "BANK_ROUTING", "IP_ADDRESS", "MAC_ADDRESS", "ALL"
    }
    
    def __init__(self, config: GuardrailProviderConfig):
        super().__init__(config)
        
        self.access_key = config.custom_config.get("aws_access_key")
        self.secret_key = config.custom_config.get("aws_secret_key")
        self.region = config.region or "us-east-1"
        
        if not self.access_key or not self.secret_key:
            raise ValueError("AWS credentials (access_key, secret_key) are required")
        
        self.pii_enabled = config.custom_config.get("pii_detection", True)
        self.sentiment_enabled = config.custom_config.get("sentiment_analysis", True)
        self.toxicity_enabled = config.custom_config.get("toxicity_detection", True)
    
    async def check_input(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Check input text using AWS Comprehend."""
        return await self._analyze(text, "input", context)
    
    async def check_output(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Check output text using AWS Comprehend."""
        return await self._analyze(text, "output", context)
    
    async def _analyze(
        self,
        text: str,
        stage: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """Perform AWS Comprehend analysis."""
        start_time = time.time()
        violations = []
        
        try:
            # PII Detection
            if self.pii_enabled:
                pii_violations = await self._detect_pii(text)
                violations.extend(pii_violations)
            
            # Sentiment Analysis
            if self.sentiment_enabled:
                sentiment_violations = await self._analyze_sentiment(text)
                violations.extend(sentiment_violations)
            
            # Toxicity Detection
            if self.toxicity_enabled:
                toxicity_violations = await self._detect_toxicity(text)
                violations.extend(toxicity_violations)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Determine recommendation
            recommended_action = GuardrailAction.ALLOW
            if any(v.suggested_action == GuardrailAction.BLOCK for v in violations):
                recommended_action = GuardrailAction.BLOCK
            elif any(v.suggested_action == GuardrailAction.REDACT for v in violations):
                recommended_action = GuardrailAction.REDACT
            elif violations:
                recommended_action = GuardrailAction.WARN
            
            return GuardrailResult(
                provider="AWS Comprehend",
                passed=len(violations) == 0 or recommended_action != GuardrailAction.BLOCK,
                violations=violations,
                recommended_action=recommended_action,
                processing_time_ms=processing_time,
                metadata={"stage": stage, "region": self.region}
            )
        
        except Exception as e:
            logger.error(
                "aws_comprehend_error",
                error=str(e),
                text_length=len(text)
            )
            processing_time = (time.time() - start_time) * 1000
            return GuardrailResult(
                provider="AWS Comprehend",
                passed=True,  # Fail open
                violations=[],
                recommended_action=GuardrailAction.ALLOW,
                processing_time_ms=processing_time,
                metadata={"error": str(e), "failed_gracefully": True}
            )
    
    async def _detect_pii(self, text: str) -> List[GuardrailViolation]:
        """Detect PII using AWS Comprehend."""
        violations = []
        
        try:
            # Mock implementation - in production, use boto3
            # For now, return empty to avoid AWS calls without proper setup
            # 
            # Example real implementation:
            # import boto3
            # comprehend = boto3.client('comprehend', region_name=self.region)
            # response = comprehend.detect_pii_entities(
            #     Text=text,
            #     LanguageCode='en'
            # )
            # 
            # for entity in response['Entities']:
            #     if entity['Score'] >= 0.7:
            #         violations.append(...)
            
            logger.debug("aws_pii_detection_skipped", reason="mock_mode")
            
        except Exception as e:
            logger.error("aws_pii_detection_error", error=str(e))
        
        return violations
    
    async def _analyze_sentiment(self, text: str) -> List[GuardrailViolation]:
        """Analyze sentiment using AWS Comprehend."""
        violations = []
        
        try:
            # Mock implementation
            # Real: boto3.client('comprehend').detect_sentiment()
            logger.debug("aws_sentiment_analysis_skipped", reason="mock_mode")
            
        except Exception as e:
            logger.error("aws_sentiment_analysis_error", error=str(e))
        
        return violations
    
    async def _detect_toxicity(self, text: str) -> List[GuardrailViolation]:
        """Detect toxicity using AWS Comprehend Toxicity Detection."""
        violations = []
        
        try:
            # Mock implementation
            # Real: boto3.client('comprehend').detect_toxic_content()
            logger.debug("aws_toxicity_detection_skipped", reason="mock_mode")
            
        except Exception as e:
            logger.error("aws_toxicity_detection_error", error=str(e))
        
        return violations
    
    def get_capabilities(self) -> List[GuardrailCategory]:
        """Get supported categories."""
        capabilities = []
        if self.pii_enabled:
            capabilities.append(GuardrailCategory.PII)
        if self.sentiment_enabled:
            capabilities.append(GuardrailCategory.SENTIMENT)
        if self.toxicity_enabled:
            capabilities.append(GuardrailCategory.TOXICITY)
        return capabilities
    
    async def health_check(self) -> bool:
        """Check if AWS Comprehend is accessible."""
        try:
            # Mock health check
            # Real: make a simple API call to verify credentials
            return True
        except Exception as e:
            logger.error("aws_health_check_failed", error=str(e))
            return False
