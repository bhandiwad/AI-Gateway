"""
Centralized Error Handler for AI Gateway

Provides standardized error handling, categorization, and user-friendly messages
for various error scenarios including:
- Provider errors (quota, payment, rate limits)
- Gateway errors (cost limits, circuit breaker)
- Validation errors
- Authentication/authorization errors
"""

import re
from typing import Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categories of errors for better handling and display"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    COST_LIMIT = "cost_limit"
    PROVIDER_QUOTA = "provider_quota"
    PROVIDER_PAYMENT = "provider_payment"
    PROVIDER_RATE_LIMIT = "provider_rate_limit"
    PROVIDER_INVALID_REQUEST = "provider_invalid_request"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    CIRCUIT_BREAKER = "circuit_breaker"
    GUARDRAIL_VIOLATION = "guardrail_violation"
    VALIDATION = "validation"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ErrorResponse:
    """Standardized error response structure"""
    
    def __init__(
        self,
        category: ErrorCategory,
        message: str,
        user_message: str,
        http_status: int,
        retry_after: Optional[int] = None,
        details: Optional[Dict] = None,
        suggested_action: Optional[str] = None
    ):
        self.category = category
        self.message = message  # Technical message for logs
        self.user_message = user_message  # User-friendly message
        self.http_status = http_status
        self.retry_after = retry_after  # Seconds to wait before retry
        self.details = details or {}
        self.suggested_action = suggested_action
    
    def to_dict(self) -> Dict:
        """Convert to API response format"""
        response = {
            "error": {
                "type": self.category.value,
                "message": self.user_message,
                "details": self.details
            }
        }
        
        if self.retry_after:
            response["error"]["retry_after_seconds"] = self.retry_after
        
        if self.suggested_action:
            response["error"]["suggested_action"] = self.suggested_action
        
        return response


class AIGatewayErrorHandler:
    """
    Centralized error handler that categorizes and formats errors
    for consistent client experience
    """
    
    # Provider-specific error patterns
    PROVIDER_ERROR_PATTERNS = {
        # OpenAI errors
        "insufficient_quota": {
            "patterns": [
                r"exceeded your current quota",
                r"insufficient_quota",
                r"quota.*exceeded",
                r"billing hard limit"
            ],
            "category": ErrorCategory.PROVIDER_QUOTA,
            "user_message": "The AI provider has reached its usage quota. Please contact support to increase limits.",
            "suggested_action": "Add payment method or increase quota limits in provider dashboard"
        },
        "payment_required": {
            "patterns": [
                r"payment.*required",
                r"billing.*issue",
                r"credit card.*declined",
                r"payment.*failed",
                r"account.*suspended.*payment"
            ],
            "category": ErrorCategory.PROVIDER_PAYMENT,
            "user_message": "The AI provider account has a payment issue. Please update payment information.",
            "suggested_action": "Update payment method in provider dashboard"
        },
        "provider_rate_limit": {
            "patterns": [
                r"rate.*limit.*exceeded",
                r"too many requests",
                r"429",
                r"requests per minute"
            ],
            "category": ErrorCategory.PROVIDER_RATE_LIMIT,
            "user_message": "The AI provider's rate limit has been exceeded. Please try again in a moment.",
            "suggested_action": "Wait and retry, or upgrade provider plan for higher rate limits"
        },
        "invalid_api_key": {
            "patterns": [
                r"invalid.*api.*key",
                r"authentication.*failed",
                r"unauthorized",
                r"401"
            ],
            "category": ErrorCategory.AUTHENTICATION,
            "user_message": "The AI provider credentials are invalid. Please check API key configuration.",
            "suggested_action": "Update provider API key in gateway settings"
        },
        "model_not_found": {
            "patterns": [
                r"model.*not found",
                r"model.*does not exist",
                r"model.*not available",
                r"404.*model"
            ],
            "category": ErrorCategory.PROVIDER_INVALID_REQUEST,
            "user_message": "The requested AI model is not available with your current provider plan.",
            "suggested_action": "Check available models or upgrade provider plan"
        },
        "provider_unavailable": {
            "patterns": [
                r"503",
                r"service unavailable",
                r"temporarily unavailable",
                r"server error",
                r"504",
                r"gateway timeout"
            ],
            "category": ErrorCategory.PROVIDER_UNAVAILABLE,
            "user_message": "The AI provider is temporarily unavailable. The request will be retried automatically.",
            "suggested_action": "Wait for automatic retry or try again later"
        },
        "content_filter": {
            "patterns": [
                r"content.*filter",
                r"content.*policy.*violated",
                r"responsible ai policy"
            ],
            "category": ErrorCategory.GUARDRAIL_VIOLATION,
            "user_message": "The request was blocked by the AI provider's content policy.",
            "suggested_action": "Modify the request to comply with content guidelines"
        }
    }
    
    def categorize_error(self, error: Exception) -> ErrorResponse:
        """
        Categorize an error and return a standardized error response.
        
        Args:
            error: The exception that was raised
            
        Returns:
            ErrorResponse with category, user message, and suggested actions
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Check circuit breaker errors
        if "circuit breaker" in error_str or "circuit" in error_str:
            return ErrorResponse(
                category=ErrorCategory.CIRCUIT_BREAKER,
                message=str(error),
                user_message="The AI provider is currently unavailable due to repeated failures. Trying alternative providers.",
                http_status=503,
                retry_after=30,
                suggested_action="Wait 30 seconds for automatic recovery or try a different model"
            )
        
        # Check against provider error patterns
        for error_key, error_config in self.PROVIDER_ERROR_PATTERNS.items():
            for pattern in error_config["patterns"]:
                if re.search(pattern, error_str, re.IGNORECASE):
                    return ErrorResponse(
                        category=error_config["category"],
                        message=str(error),
                        user_message=error_config["user_message"],
                        http_status=self._get_http_status(error_config["category"]),
                        retry_after=self._get_retry_after(error_config["category"]),
                        suggested_action=error_config.get("suggested_action")
                    )
        
        # Check for rate limiting (Gateway-level)
        if "rate limit" in error_str:
            return ErrorResponse(
                category=ErrorCategory.RATE_LIMIT,
                message=str(error),
                user_message="You have exceeded the rate limit. Please wait before making more requests.",
                http_status=429,
                retry_after=60,
                suggested_action="Wait 60 seconds or upgrade to a higher rate limit tier"
            )
        
        # Check for cost limits (Gateway-level)
        if "cost limit" in error_str or "budget" in error_str:
            return ErrorResponse(
                category=ErrorCategory.COST_LIMIT,
                message=str(error),
                user_message="Your cost limit has been reached. Please contact your administrator.",
                http_status=402,  # Payment Required
                suggested_action="Increase cost limits or add more budget"
            )
        
        # Check for authentication errors
        if any(x in error_str for x in ["unauthorized", "invalid.*key", "authentication"]):
            return ErrorResponse(
                category=ErrorCategory.AUTHENTICATION,
                message=str(error),
                user_message="Authentication failed. Please check your API key.",
                http_status=401,
                suggested_action="Verify your API key is correct and active"
            )
        
        # Check for guardrail violations
        if "guardrail" in error_str or "blocked" in error_str or "violation" in error_str:
            return ErrorResponse(
                category=ErrorCategory.GUARDRAIL_VIOLATION,
                message=str(error),
                user_message="The request was blocked by content safety guardrails.",
                http_status=400,
                details=self._extract_guardrail_details(str(error)),
                suggested_action="Modify the request to comply with safety policies"
            )
        
        # Default to internal error
        return ErrorResponse(
            category=ErrorCategory.INTERNAL,
            message=str(error),
            user_message="An unexpected error occurred. Our team has been notified.",
            http_status=500,
            suggested_action="Please try again or contact support if the issue persists"
        )
    
    def _get_http_status(self, category: ErrorCategory) -> int:
        """Map error category to appropriate HTTP status code"""
        status_map = {
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.AUTHORIZATION: 403,
            ErrorCategory.RATE_LIMIT: 429,
            ErrorCategory.COST_LIMIT: 402,
            ErrorCategory.PROVIDER_QUOTA: 429,
            ErrorCategory.PROVIDER_PAYMENT: 402,
            ErrorCategory.PROVIDER_RATE_LIMIT: 429,
            ErrorCategory.PROVIDER_INVALID_REQUEST: 400,
            ErrorCategory.PROVIDER_UNAVAILABLE: 503,
            ErrorCategory.CIRCUIT_BREAKER: 503,
            ErrorCategory.GUARDRAIL_VIOLATION: 400,
            ErrorCategory.VALIDATION: 400,
            ErrorCategory.INTERNAL: 500,
            ErrorCategory.UNKNOWN: 500
        }
        return status_map.get(category, 500)
    
    def _get_retry_after(self, category: ErrorCategory) -> Optional[int]:
        """Get recommended retry delay for error category"""
        retry_map = {
            ErrorCategory.RATE_LIMIT: 60,
            ErrorCategory.PROVIDER_RATE_LIMIT: 30,
            ErrorCategory.PROVIDER_UNAVAILABLE: 10,
            ErrorCategory.CIRCUIT_BREAKER: 30
        }
        return retry_map.get(category)
    
    def _extract_guardrail_details(self, error_message: str) -> Dict:
        """Extract details from guardrail violation messages"""
        details = {}
        
        # Try to extract triggered rule
        rule_match = re.search(r"triggered.*?:?\s*([^\.]+)", error_message, re.IGNORECASE)
        if rule_match:
            details["triggered_rule"] = rule_match.group(1).strip()
        
        # Try to extract category
        category_match = re.search(r"category:?\s*([a-z_]+)", error_message, re.IGNORECASE)
        if category_match:
            details["category"] = category_match.group(1).strip()
        
        return details
    
    def format_error_for_logging(self, error_response: ErrorResponse) -> Dict:
        """Format error for structured logging"""
        return {
            "error_category": error_response.category.value,
            "error_message": error_response.message,
            "user_message": error_response.user_message,
            "http_status": error_response.http_status,
            "retry_after": error_response.retry_after,
            "suggested_action": error_response.suggested_action,
            "details": error_response.details
        }
    
    def should_retry(self, error_response: ErrorResponse) -> Tuple[bool, int]:
        """
        Determine if error should trigger automatic retry and after how long.
        
        Returns:
            Tuple of (should_retry, wait_seconds)
        """
        retryable_categories = {
            ErrorCategory.PROVIDER_RATE_LIMIT,
            ErrorCategory.PROVIDER_UNAVAILABLE,
            ErrorCategory.CIRCUIT_BREAKER
        }
        
        should_retry = error_response.category in retryable_categories
        wait_seconds = error_response.retry_after or 5
        
        return should_retry, wait_seconds


# Global error handler instance
error_handler = AIGatewayErrorHandler()
