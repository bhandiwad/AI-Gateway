import re
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import structlog

logger = structlog.get_logger()


class ContentCategory(str, Enum):
    CODING = "coding"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    MATH = "math"
    GENERAL = "general"
    CUSTOMER_SERVICE = "customer_service"
    FINANCIAL = "financial"
    LEGAL = "legal"
    MEDICAL = "medical"
    TECHNICAL = "technical"


DEFAULT_ROUTING_RULES = {
    ContentCategory.CODING: {
        "preferred_models": ["claude-3-5-sonnet-20241022", "gpt-4o", "gpt-4-turbo"],
        "fallback_model": "gpt-4o-mini",
        "priority": 1
    },
    ContentCategory.CREATIVE: {
        "preferred_models": ["gpt-4o", "claude-3-opus-20240229"],
        "fallback_model": "gpt-4o-mini",
        "priority": 2
    },
    ContentCategory.ANALYSIS: {
        "preferred_models": ["claude-3-5-sonnet-20241022", "gpt-4o"],
        "fallback_model": "gpt-4o-mini",
        "priority": 1
    },
    ContentCategory.MATH: {
        "preferred_models": ["gpt-4o", "claude-3-5-sonnet-20241022"],
        "fallback_model": "gpt-4o-mini",
        "priority": 1
    },
    ContentCategory.FINANCIAL: {
        "preferred_models": ["gpt-4o", "claude-3-5-sonnet-20241022"],
        "fallback_model": "gpt-4o-mini",
        "priority": 1
    },
    ContentCategory.LEGAL: {
        "preferred_models": ["claude-3-opus-20240229", "gpt-4o"],
        "fallback_model": "gpt-4o-mini",
        "priority": 2
    },
    ContentCategory.MEDICAL: {
        "preferred_models": ["gpt-4o", "claude-3-opus-20240229"],
        "fallback_model": "gpt-4o-mini",
        "priority": 2
    },
    ContentCategory.TECHNICAL: {
        "preferred_models": ["claude-3-5-sonnet-20241022", "gpt-4o"],
        "fallback_model": "gpt-4o-mini",
        "priority": 1
    },
    ContentCategory.CUSTOMER_SERVICE: {
        "preferred_models": ["gpt-4o-mini", "claude-3-haiku-20240307"],
        "fallback_model": "gpt-3.5-turbo",
        "priority": 3
    },
    ContentCategory.GENERAL: {
        "preferred_models": ["gpt-4o-mini", "claude-3-haiku-20240307"],
        "fallback_model": "gpt-3.5-turbo",
        "priority": 3
    }
}


CATEGORY_PATTERNS = {
    ContentCategory.CODING: [
        r'\b(code|programming|function|class|method|api|debug|compile|syntax|algorithm|git|docker|kubernetes)\b',
        r'\b(python|javascript|typescript|java|c\+\+|rust|go|ruby|php|sql|html|css)\b',
        r'\b(implement|refactor|optimize|fix bug|write a script|parse|regex)\b',
        r'```[\s\S]*?```',
        r'\b(npm|pip|cargo|maven|gradle|webpack|vite)\b',
    ],
    ContentCategory.CREATIVE: [
        r'\b(write|story|poem|creative|fiction|narrative|character|plot|dialogue)\b',
        r'\b(imagine|describe creatively|metaphor|artistic|literary|compose)\b',
        r'\b(novel|short story|screenplay|lyrics|haiku|sonnet)\b',
    ],
    ContentCategory.ANALYSIS: [
        r'\b(analyze|analysis|evaluate|assess|review|examine|compare|contrast)\b',
        r'\b(data|statistics|trends|patterns|insights|metrics|kpis)\b',
        r'\b(report|summary|findings|conclusions|recommendations)\b',
    ],
    ContentCategory.MATH: [
        r'\b(calculate|equation|formula|derivative|integral|algebra|calculus)\b',
        r'\b(probability|statistics|matrix|vector|geometry|trigonometry)\b',
        r'[\d\s\+\-\*\/\=\(\)]{5,}',
        r'\b(solve|compute|prove|theorem|lemma)\b',
    ],
    ContentCategory.FINANCIAL: [
        r'\b(finance|financial|investment|stock|bond|portfolio|roi|revenue)\b',
        r'\b(balance sheet|income statement|cash flow|earnings|dividend)\b',
        r'\b(banking|loan|mortgage|interest rate|credit|debit)\b',
        r'\b(hedge|derivative|option|futures|forex|crypto|bitcoin)\b',
        r'\b(audit|compliance|sox|gaap|ifrs|regulatory)\b',
    ],
    ContentCategory.LEGAL: [
        r'\b(legal|law|attorney|lawyer|court|litigation|contract)\b',
        r'\b(clause|agreement|terms|conditions|liability|indemnity)\b',
        r'\b(compliance|regulation|statute|jurisdiction|precedent)\b',
        r'\b(plaintiff|defendant|verdict|settlement|arbitration)\b',
    ],
    ContentCategory.MEDICAL: [
        r'\b(medical|health|clinical|diagnosis|treatment|symptom)\b',
        r'\b(patient|doctor|physician|nurse|hospital|medication)\b',
        r'\b(disease|condition|therapy|prescription|dosage)\b',
        r'\b(surgery|procedure|lab results|imaging|biopsy)\b',
    ],
    ContentCategory.TECHNICAL: [
        r'\b(technical|engineering|architecture|infrastructure|system)\b',
        r'\b(network|server|database|cloud|aws|azure|gcp)\b',
        r'\b(security|encryption|authentication|firewall|vpn)\b',
        r'\b(performance|scalability|reliability|latency|throughput)\b',
    ],
    ContentCategory.CUSTOMER_SERVICE: [
        r'\b(help|support|issue|problem|question|complaint)\b',
        r'\b(customer|client|user|account|order|refund|return)\b',
        r'\b(thank you|please|sorry|apologize|assist)\b',
    ],
}


class ContentRoutingService:
    def __init__(self):
        self.routing_rules = DEFAULT_ROUTING_RULES.copy()
        self._tenant_overrides: Dict[int, Dict[str, Any]] = {}
        self._compiled_patterns = {}
        
        for category, patterns in CATEGORY_PATTERNS.items():
            self._compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        
        logger.info("content_routing_service_initialized")
    
    def detect_content_category(
        self,
        messages: List[Dict[str, Any]]
    ) -> Tuple[ContentCategory, float]:
        text = self._extract_text(messages)
        
        category_scores: Dict[ContentCategory, float] = {}
        
        for category, patterns in self._compiled_patterns.items():
            score = 0
            for pattern in patterns:
                matches = pattern.findall(text)
                score += len(matches)
            
            if category == ContentCategory.CODING:
                if '```' in text or 'def ' in text or 'function ' in text:
                    score += 5
            
            category_scores[category] = score
        
        max_score = max(category_scores.values()) if category_scores else 0
        
        if max_score < 2:
            return ContentCategory.GENERAL, 0.5
        
        detected_category = max(category_scores, key=lambda k: category_scores[k])
        
        total_score = sum(category_scores.values())
        confidence = category_scores[detected_category] / total_score if total_score > 0 else 0.5
        
        return detected_category, min(confidence, 1.0)
    
    def _extract_text(self, messages: List[Dict[str, Any]]) -> str:
        texts = []
        for msg in messages[-3:]:
            content = msg.get("content", "")
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        texts.append(item.get("text", ""))
        return " ".join(texts)
    
    def get_recommended_model(
        self,
        messages: List[Dict[str, Any]],
        requested_model: Optional[str] = None,
        tenant_id: Optional[int] = None,
        available_models: Optional[List[str]] = None
    ) -> Tuple[str, ContentCategory, Dict[str, Any]]:
        category, confidence = self.detect_content_category(messages)
        
        routing_rules = self.routing_rules.copy()
        if tenant_id and tenant_id in self._tenant_overrides:
            for cat, rules in self._tenant_overrides[tenant_id].items():
                if cat in routing_rules:
                    routing_rules[cat].update(rules)
        
        routing_decision = {
            "detected_category": category.value,
            "confidence": round(confidence, 3),
            "requested_model": requested_model,
            "routing_applied": False,
            "reason": ""
        }
        
        if requested_model:
            routing_decision["selected_model"] = requested_model
            routing_decision["reason"] = "User specified model"
            return requested_model, category, routing_decision
        
        category_rules = routing_rules.get(category, routing_rules[ContentCategory.GENERAL])
        preferred_models = category_rules.get("preferred_models", [])
        fallback_model = category_rules.get("fallback_model", "gpt-4o-mini")
        
        if available_models:
            for model in preferred_models:
                if model in available_models:
                    routing_decision["selected_model"] = model
                    routing_decision["routing_applied"] = True
                    routing_decision["reason"] = f"Content-based routing for {category.value}"
                    return model, category, routing_decision
            
            if fallback_model in available_models:
                routing_decision["selected_model"] = fallback_model
                routing_decision["routing_applied"] = True
                routing_decision["reason"] = f"Fallback model for {category.value}"
                return fallback_model, category, routing_decision
        
        selected = preferred_models[0] if preferred_models else fallback_model
        routing_decision["selected_model"] = selected
        routing_decision["routing_applied"] = True
        routing_decision["reason"] = f"Default routing for {category.value}"
        
        return selected, category, routing_decision
    
    def set_tenant_routing_override(
        self,
        tenant_id: int,
        category: ContentCategory,
        preferred_models: Optional[List[str]] = None,
        fallback_model: Optional[str] = None
    ):
        if tenant_id not in self._tenant_overrides:
            self._tenant_overrides[tenant_id] = {}
        
        override = {}
        if preferred_models:
            override["preferred_models"] = preferred_models
        if fallback_model:
            override["fallback_model"] = fallback_model
        
        self._tenant_overrides[tenant_id][category.value] = override
        
        logger.info(
            "tenant_routing_override_set",
            tenant_id=tenant_id,
            category=category.value,
            override=override
        )
    
    def get_tenant_routing_config(self, tenant_id: int) -> Dict[str, Any]:
        base_config = {
            cat.value: {
                "preferred_models": rules["preferred_models"],
                "fallback_model": rules["fallback_model"]
            }
            for cat, rules in self.routing_rules.items()
        }
        
        if tenant_id in self._tenant_overrides:
            for cat_key, override in self._tenant_overrides[tenant_id].items():
                if cat_key in base_config:
                    base_config[cat_key].update(override)
        
        return {
            "tenant_id": tenant_id,
            "routing_rules": base_config,
            "categories": [c.value for c in ContentCategory]
        }
    
    def get_routing_stats(self) -> Dict[str, Any]:
        return {
            "categories": [c.value for c in ContentCategory],
            "tenants_with_overrides": len(self._tenant_overrides),
            "default_rules_count": len(self.routing_rules)
        }


content_routing_service = ContentRoutingService()
