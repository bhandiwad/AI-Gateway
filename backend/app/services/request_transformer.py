"""
Request/Response Transformer Service for AI Gateway

Provides flexible transformation of requests and responses:
- Request transformations: headers, body fields, system prompts
- Response transformations: field filtering, metadata injection, normalization
- Per-route transformation rules
- Lambda-style field transformations

Use cases:
- Inject company-wide system prompts
- Hide internal provider details
- Normalize response formats across providers
- Add compliance metadata
- Cap/modify parameters (temperature, max_tokens)
"""

import re
import json
import copy
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TransformationRule:
    """Defines a single transformation rule"""
    field_path: str                    # JSONPath-style field selector (e.g., "messages.0.content")
    operation: str                     # add, remove, replace, modify
    value: Any = None                  # Static value or lambda expression
    condition: Optional[str] = None    # Optional condition (e.g., "field > 0.8")


class RequestTransformer:
    """
    Transforms incoming requests based on configured rules.
    Supports field injection, modification, and validation.
    """
    
    def __init__(self):
        self._route_rules: Dict[str, List[TransformationRule]] = {}
    
    def register_route_rules(self, route_path: str, rules: List[Dict]):
        """
        Register transformation rules for a specific route.
        
        Args:
            route_path: API route path (e.g., "/v1/chat/completions")
            rules: List of transformation rule configs
        """
        self._route_rules[route_path] = [
            TransformationRule(
                field_path=r["field_path"],
                operation=r["operation"],
                value=r.get("value"),
                condition=r.get("condition")
            )
            for r in rules
        ]
        logger.info(f"Registered {len(rules)} transformation rules for route '{route_path}'")
    
    def transform_request(
        self,
        route_path: str,
        request_data: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Transform request based on route-specific rules.
        
        Args:
            route_path: API route path
            request_data: Original request data
            context: Additional context (tenant_id, api_key_id, etc.)
            
        Returns:
            Transformed request data
        """
        rules = self._route_rules.get(route_path, [])
        if not rules:
            return request_data
        
        # Deep copy to avoid mutating original
        transformed = copy.deepcopy(request_data)
        context = context or {}
        
        for rule in rules:
            try:
                transformed = self._apply_rule(transformed, rule, context)
            except Exception as e:
                logger.error(f"Failed to apply transformation rule {rule.field_path}: {e}")
        
        return transformed
    
    def _apply_rule(
        self,
        data: Dict[str, Any],
        rule: TransformationRule,
        context: Dict
    ) -> Dict[str, Any]:
        """Apply a single transformation rule"""
        
        # Check condition if present
        if rule.condition and not self._evaluate_condition(data, rule.condition, context):
            return data
        
        if rule.operation == "add" or rule.operation == "set":
            return self._set_field(data, rule.field_path, rule.value, context)
        
        elif rule.operation == "remove":
            return self._remove_field(data, rule.field_path)
        
        elif rule.operation == "modify":
            return self._modify_field(data, rule.field_path, rule.value, context)
        
        elif rule.operation == "inject_system_prompt":
            return self._inject_system_prompt(data, rule.value)
        
        elif rule.operation == "cap_value":
            return self._cap_value(data, rule.field_path, rule.value)
        
        elif rule.operation == "enforce_min":
            return self._enforce_min(data, rule.field_path, rule.value)
        
        else:
            logger.warning(f"Unknown transformation operation: {rule.operation}")
            return data
    
    def _set_field(
        self,
        data: Dict,
        field_path: str,
        value: Any,
        context: Dict
    ) -> Dict:
        """Set a field value (supports nested paths)"""
        parts = field_path.split(".")
        current = data
        
        # Navigate to parent
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Resolve value (support context variables)
        resolved_value = self._resolve_value(value, context)
        current[parts[-1]] = resolved_value
        
        logger.debug(f"Set field '{field_path}' = {resolved_value}")
        return data
    
    def _remove_field(self, data: Dict, field_path: str) -> Dict:
        """Remove a field"""
        parts = field_path.split(".")
        current = data
        
        try:
            # Navigate to parent
            for part in parts[:-1]:
                current = current[part]
            
            # Remove field
            if parts[-1] in current:
                del current[parts[-1]]
                logger.debug(f"Removed field '{field_path}'")
        except (KeyError, TypeError):
            pass  # Field doesn't exist, no-op
        
        return data
    
    def _modify_field(
        self,
        data: Dict,
        field_path: str,
        modifier: Any,
        context: Dict
    ) -> Dict:
        """Modify a field using a lambda expression or function"""
        parts = field_path.split(".")
        current = data
        
        try:
            # Navigate to parent
            for part in parts[:-1]:
                current = current[part]
            
            field_name = parts[-1]
            if field_name in current:
                old_value = current[field_name]
                
                # Apply modifier
                if isinstance(modifier, str) and modifier.startswith("lambda"):
                    # Evaluate lambda (careful - security risk in production)
                    # In production, use pre-defined functions instead
                    func = eval(modifier)
                    new_value = func(old_value)
                elif callable(modifier):
                    new_value = modifier(old_value)
                else:
                    new_value = modifier
                
                current[field_name] = new_value
                logger.debug(f"Modified field '{field_path}': {old_value} → {new_value}")
        except Exception as e:
            logger.error(f"Failed to modify field '{field_path}': {e}")
        
        return data
    
    def _inject_system_prompt(self, data: Dict, system_prompt: str) -> Dict:
        """Inject or prepend a system prompt to messages"""
        if "messages" not in data:
            return data
        
        messages = data["messages"]
        
        # Check if system message already exists
        has_system = any(msg.get("role") == "system" for msg in messages)
        
        if not has_system:
            # Add system prompt at the beginning
            messages.insert(0, {"role": "system", "content": system_prompt})
            logger.debug(f"Injected system prompt: {system_prompt[:50]}...")
        else:
            # Prepend to existing system message
            for msg in messages:
                if msg.get("role") == "system":
                    msg["content"] = f"{system_prompt}\n\n{msg['content']}"
                    logger.debug("Prepended to existing system prompt")
                    break
        
        return data
    
    def _cap_value(self, data: Dict, field_path: str, max_value: float) -> Dict:
        """Cap a numeric field to a maximum value"""
        parts = field_path.split(".")
        current = data
        
        try:
            for part in parts[:-1]:
                current = current[part]
            
            field_name = parts[-1]
            if field_name in current:
                old_value = current[field_name]
                if isinstance(old_value, (int, float)):
                    new_value = min(old_value, max_value)
                    current[field_name] = new_value
                    if old_value != new_value:
                        logger.debug(f"Capped '{field_path}': {old_value} → {new_value}")
        except (KeyError, TypeError):
            pass
        
        return data
    
    def _enforce_min(self, data: Dict, field_path: str, min_value: float) -> Dict:
        """Enforce minimum value for a numeric field"""
        parts = field_path.split(".")
        current = data
        
        try:
            for part in parts[:-1]:
                current = current[part]
            
            field_name = parts[-1]
            if field_name in current:
                old_value = current[field_name]
                if isinstance(old_value, (int, float)):
                    new_value = max(old_value, min_value)
                    current[field_name] = new_value
                    if old_value != new_value:
                        logger.debug(f"Enforced min '{field_path}': {old_value} → {new_value}")
        except (KeyError, TypeError):
            pass
        
        return data
    
    def _evaluate_condition(self, data: Dict, condition: str, context: Dict) -> bool:
        """Evaluate a condition string (simplified)"""
        # Simplified condition evaluation
        # In production, use a proper expression parser
        try:
            # Support simple comparisons like "temperature > 0.8"
            if ">" in condition:
                field, value = condition.split(">")
                field_value = self._get_field_value(data, field.strip())
                return float(field_value) > float(value.strip())
            elif "<" in condition:
                field, value = condition.split("<")
                field_value = self._get_field_value(data, field.strip())
                return float(field_value) < float(value.strip())
            elif "==" in condition:
                field, value = condition.split("==")
                field_value = self._get_field_value(data, field.strip())
                return str(field_value) == value.strip().strip('"\'')
        except Exception:
            return False
        
        return True
    
    def _get_field_value(self, data: Dict, field_path: str) -> Any:
        """Get value of a nested field"""
        parts = field_path.split(".")
        current = data
        for part in parts:
            current = current[part]
        return current
    
    def _resolve_value(self, value: Any, context: Dict) -> Any:
        """Resolve value with context variable substitution"""
        if isinstance(value, str) and "{" in value:
            # Simple template substitution
            for key, val in context.items():
                value = value.replace(f"{{{key}}}", str(val))
        return value


class ResponseTransformer:
    """
    Transforms outgoing responses based on configured rules.
    Supports field filtering, metadata injection, and normalization.
    """
    
    def __init__(self):
        self._route_rules: Dict[str, Dict] = {}
    
    def register_route_rules(self, route_path: str, rules: Dict):
        """
        Register response transformation rules for a route.
        
        Args:
            route_path: API route path
            rules: Response transformation config with keys:
                   - filter_fields: List of fields to remove
                   - add_metadata: Dict of metadata to add
                   - normalize_format: Provider-specific normalization
        """
        self._route_rules[route_path] = rules
        logger.info(f"Registered response transformation rules for route '{route_path}'")
    
    def transform_response(
        self,
        route_path: str,
        response_data: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Transform response based on route-specific rules.
        
        Args:
            route_path: API route path
            response_data: Original response data
            context: Additional context
            
        Returns:
            Transformed response data
        """
        rules = self._route_rules.get(route_path, {})
        if not rules:
            return response_data
        
        # Deep copy to avoid mutating original
        transformed = copy.deepcopy(response_data)
        context = context or {}
        
        # Apply filter_fields
        if "filter_fields" in rules:
            for field_path in rules["filter_fields"]:
                transformed = self._remove_field(transformed, field_path)
        
        # Apply add_metadata
        if "add_metadata" in rules:
            for key, value in rules["add_metadata"].items():
                resolved_value = self._resolve_value(value, context)
                transformed[key] = resolved_value
        
        # Apply field modifications
        if "modify_fields" in rules:
            for field_path, modifier in rules["modify_fields"].items():
                transformed = self._modify_field(transformed, field_path, modifier, context)
        
        # Normalize provider-specific formats
        if rules.get("normalize_format"):
            transformed = self._normalize_format(transformed, context)
        
        return transformed
    
    def _remove_field(self, data: Dict, field_path: str) -> Dict:
        """Remove a field from response"""
        parts = field_path.split(".")
        current = data
        
        try:
            for part in parts[:-1]:
                current = current[part]
            
            if parts[-1] in current:
                del current[parts[-1]]
                logger.debug(f"Filtered out field '{field_path}'")
        except (KeyError, TypeError, IndexError):
            pass
        
        return data
    
    def _modify_field(
        self,
        data: Dict,
        field_path: str,
        modifier: Any,
        context: Dict
    ) -> Dict:
        """Modify a response field"""
        parts = field_path.split(".")
        current = data
        
        try:
            for part in parts[:-1]:
                current = current[part]
            
            field_name = parts[-1]
            if field_name in current:
                old_value = current[field_name]
                
                if isinstance(modifier, str) and modifier.startswith("lambda"):
                    func = eval(modifier)
                    new_value = func(old_value)
                elif callable(modifier):
                    new_value = modifier(old_value)
                else:
                    new_value = modifier
                
                current[field_name] = new_value
                logger.debug(f"Modified response field '{field_path}'")
        except Exception as e:
            logger.error(f"Failed to modify response field '{field_path}': {e}")
        
        return data
    
    def _normalize_format(self, data: Dict, context: Dict) -> Dict:
        """Normalize provider-specific response formats to standard format"""
        # Add provider-agnostic normalization here
        # E.g., ensure all responses have consistent structure
        
        if "model" in data and context.get("hide_provider"):
            # Hide real provider name
            data["model"] = re.sub(r'^(openai|anthropic|google)/', '', data["model"])
        
        return data
    
    def _resolve_value(self, value: Any, context: Dict) -> Any:
        """Resolve value with context variable substitution"""
        if isinstance(value, str) and "{" in value:
            for key, val in context.items():
                value = value.replace(f"{{{key}}}", str(val))
        return value


# Global transformer instances
request_transformer = RequestTransformer()
response_transformer = ResponseTransformer()
