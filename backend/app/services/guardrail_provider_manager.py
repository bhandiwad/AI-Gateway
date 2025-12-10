from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import structlog
import asyncio

from backend.app.services.guardrail_providers import (
    BaseGuardrailProvider,
    GuardrailResult,
    GuardrailViolation,
    GuardrailAction,
    GuardrailProviderConfig,
    OpenAIGuardrailProvider,
    AWSComprehendProvider,
    GoogleCloudNLPProvider,
    AzureContentSafetyProvider
)

logger = structlog.get_logger()


class GuardrailProviderManager:
    """
    Manager for orchestrating multiple guardrail providers.
    
    Supports:
    - Multiple providers running in parallel or priority order
    - Consensus mode (require multiple providers to agree)
    - Fallback chains
    - Provider health monitoring
    """
    
    PROVIDER_CLASSES = {
        "openai": OpenAIGuardrailProvider,
        "aws_comprehend": AWSComprehendProvider,
        "google_nlp": GoogleCloudNLPProvider,
        "azure_content_safety": AzureContentSafetyProvider
    }
    
    def __init__(self):
        self.providers: Dict[str, BaseGuardrailProvider] = {}
        self.provider_priority: List[str] = []
        self.consensus_mode = False
        self.consensus_threshold = 2  # Require 2+ providers to agree
    
    def register_provider(
        self,
        provider_name: str,
        provider_type: str,
        config: GuardrailProviderConfig
    ) -> bool:
        """Register a guardrail provider."""
        try:
            if provider_type not in self.PROVIDER_CLASSES:
                logger.error(
                    "unknown_provider_type",
                    provider_type=provider_type,
                    available=list(self.PROVIDER_CLASSES.keys())
                )
                return False
            
            provider_class = self.PROVIDER_CLASSES[provider_type]
            provider = provider_class(config)
            
            self.providers[provider_name] = provider
            if provider_name not in self.provider_priority:
                self.provider_priority.append(provider_name)
            
            logger.info(
                "provider_registered",
                provider_name=provider_name,
                provider_type=provider_type,
                capabilities=provider.get_capabilities()
            )
            return True
        
        except Exception as e:
            logger.error(
                "provider_registration_failed",
                provider_name=provider_name,
                error=str(e)
            )
            return False
    
    def unregister_provider(self, provider_name: str) -> bool:
        """Unregister a guardrail provider."""
        if provider_name in self.providers:
            del self.providers[provider_name]
            if provider_name in self.provider_priority:
                self.provider_priority.remove(provider_name)
            
            logger.info("provider_unregistered", provider_name=provider_name)
            return True
        return False
    
    def set_provider_priority(self, priority_list: List[str]) -> bool:
        """Set provider execution priority."""
        for provider_name in priority_list:
            if provider_name not in self.providers:
                logger.error(
                    "invalid_provider_in_priority",
                    provider_name=provider_name
                )
                return False
        
        self.provider_priority = priority_list
        logger.info("provider_priority_updated", priority=priority_list)
        return True
    
    def enable_consensus_mode(self, threshold: int = 2):
        """Enable consensus mode where multiple providers must agree."""
        self.consensus_mode = True
        self.consensus_threshold = threshold
        logger.info(
            "consensus_mode_enabled",
            threshold=threshold
        )
    
    def disable_consensus_mode(self):
        """Disable consensus mode."""
        self.consensus_mode = False
        logger.info("consensus_mode_disabled")
    
    async def check_input(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        providers: Optional[List[str]] = None
    ) -> GuardrailResult:
        """
        Check input text across multiple providers.
        
        Args:
            text: Input text to check
            context: Additional context
            providers: Specific providers to use (None = all active)
        
        Returns:
            Aggregated GuardrailResult
        """
        return await self._check(text, "input", context, providers)
    
    async def check_output(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        providers: Optional[List[str]] = None
    ) -> GuardrailResult:
        """
        Check output text across multiple providers.
        
        Args:
            text: Output text to check
            context: Additional context
            providers: Specific providers to use (None = all active)
        
        Returns:
            Aggregated GuardrailResult
        """
        return await self._check(text, "output", context, providers)
    
    async def _check(
        self,
        text: str,
        stage: str,
        context: Optional[Dict[str, Any]] = None,
        provider_names: Optional[List[str]] = None
    ) -> GuardrailResult:
        """Internal method to check text across providers."""
        # Determine which providers to use
        if provider_names:
            active_providers = [
                (name, self.providers[name])
                for name in provider_names
                if name in self.providers and self.providers[name].config.enabled
            ]
        else:
            active_providers = [
                (name, provider)
                for name, provider in self.providers.items()
                if provider.config.enabled
            ]
        
        if not active_providers:
            logger.warning("no_active_providers")
            return GuardrailResult(
                provider="None",
                passed=True,
                violations=[],
                recommended_action=GuardrailAction.ALLOW,
                metadata={"error": "no_active_providers"}
            )
        
        # Run checks in parallel
        tasks = []
        for name, provider in active_providers:
            if stage == "input":
                tasks.append(provider.check_input(text, context))
            else:
                tasks.append(provider.check_output(text, context))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        all_violations = []
        total_processing_time = 0.0
        provider_results = []
        
        for i, result in enumerate(results):
            provider_name = active_providers[i][0]
            
            if isinstance(result, Exception):
                logger.error(
                    "provider_check_failed",
                    provider=provider_name,
                    error=str(result)
                )
                continue
            
            provider_results.append(result)
            all_violations.extend(result.violations)
            total_processing_time += result.processing_time_ms
        
        # Apply consensus logic if enabled
        if self.consensus_mode and len(provider_results) >= self.consensus_threshold:
            all_violations = self._apply_consensus(all_violations, provider_results)
        
        # Determine final recommendation
        recommended_action = GuardrailAction.ALLOW
        if any(v.suggested_action == GuardrailAction.BLOCK for v in all_violations):
            recommended_action = GuardrailAction.BLOCK
        elif any(v.suggested_action == GuardrailAction.REDACT for v in all_violations):
            recommended_action = GuardrailAction.REDACT
        elif all_violations:
            recommended_action = GuardrailAction.WARN
        
        return GuardrailResult(
            provider="Multi-Provider",
            passed=len(all_violations) == 0 or recommended_action != GuardrailAction.BLOCK,
            violations=all_violations,
            recommended_action=recommended_action,
            processing_time_ms=total_processing_time / len(provider_results) if provider_results else 0,
            metadata={
                "providers_used": [p[0] for p in active_providers],
                "providers_succeeded": len(provider_results),
                "consensus_mode": self.consensus_mode
            }
        )
    
    def _apply_consensus(
        self,
        violations: List[GuardrailViolation],
        results: List[GuardrailResult]
    ) -> List[GuardrailViolation]:
        """Apply consensus logic to violations."""
        # Group violations by category
        category_counts: Dict[str, int] = {}
        category_violations: Dict[str, List[GuardrailViolation]] = {}
        
        for violation in violations:
            cat = violation.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
            if cat not in category_violations:
                category_violations[cat] = []
            category_violations[cat].append(violation)
        
        # Only keep violations detected by threshold+ providers
        consensus_violations = []
        for category, count in category_counts.items():
            if count >= self.consensus_threshold:
                # Take the violation with highest severity
                violations_in_cat = category_violations[category]
                highest = max(violations_in_cat, key=lambda v: v.severity)
                consensus_violations.append(highest)
        
        return consensus_violations
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all registered providers."""
        results = {}
        
        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                results[name] = is_healthy
            except Exception as e:
                logger.error(
                    "provider_health_check_failed",
                    provider=name,
                    error=str(e)
                )
                results[name] = False
        
        return results
    
    def get_provider_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered providers."""
        return [
            {
                "name": name,
                **provider.get_provider_info()
            }
            for name, provider in self.providers.items()
        ]


# Global instance
guardrail_provider_manager = GuardrailProviderManager()


def get_provider_manager() -> GuardrailProviderManager:
    """Get the global guardrail provider manager instance."""
    return guardrail_provider_manager
