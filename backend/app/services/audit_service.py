from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from backend.app.db.models.audit_log import AuditLog, AuditAction, AuditSeverity


class AuditService:
    def log(
        self,
        db: Session,
        tenant_id: int,
        action: AuditAction,
        user_id: Optional[int] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            old_value=old_value,
            new_value=new_value,
            metadata_=metadata or {}
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    def log_login(
        self,
        db: Session,
        tenant_id: int,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_sso: bool = False
    ) -> AuditLog:
        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.SSO_LOGIN if is_sso else AuditAction.LOGIN,
            description=f"User logged in {'via SSO' if is_sso else 'with password'}",
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_login_failed(
        self,
        db: Session,
        tenant_id: int,
        email: str,
        ip_address: Optional[str] = None,
        reason: str = "Invalid credentials"
    ) -> AuditLog:
        return self.log(
            db=db,
            tenant_id=tenant_id,
            action=AuditAction.LOGIN_FAILED,
            severity=AuditSeverity.WARNING,
            description=f"Failed login attempt for {email}: {reason}",
            ip_address=ip_address,
            metadata={"email": email, "reason": reason}
        )

    def log_api_request(
        self,
        db: Session,
        tenant_id: int,
        user_id: Optional[int],
        request_id: str,
        model: str,
        tokens: int,
        cost: float,
        guardrail_triggered: Optional[str] = None
    ) -> AuditLog:
        severity = AuditSeverity.WARNING if guardrail_triggered else AuditSeverity.INFO
        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.API_REQUEST,
            severity=severity,
            resource_type="api_request",
            resource_id=request_id,
            description=f"API request to {model}",
            request_id=request_id,
            metadata={
                "model": model,
                "tokens": tokens,
                "cost": cost,
                "guardrail_triggered": guardrail_triggered
            }
        )

    def log_guardrail_triggered(
        self,
        db: Session,
        tenant_id: int,
        user_id: Optional[int],
        request_id: str,
        guardrail_type: str,
        action_taken: str,
        details: Optional[Dict] = None
    ) -> AuditLog:
        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.GUARDRAIL_TRIGGERED,
            severity=AuditSeverity.WARNING,
            resource_type="guardrail",
            resource_id=guardrail_type,
            description=f"Guardrail {guardrail_type} triggered, action: {action_taken}",
            request_id=request_id,
            metadata={"guardrail_type": guardrail_type, "action": action_taken, **(details or {})}
        )

    def log_config_change(
        self,
        db: Session,
        tenant_id: int,
        user_id: int,
        config_type: str,
        old_value: Optional[Dict],
        new_value: Dict
    ) -> AuditLog:
        return self.log(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CONFIG_CHANGED,
            resource_type="config",
            resource_id=config_type,
            description=f"Configuration {config_type} updated",
            old_value=old_value,
            new_value=new_value
        )

    def get_audit_logs(
        self,
        db: Session,
        tenant_id: int,
        user_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        severity: Optional[AuditSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if severity:
            query = query.filter(AuditLog.severity == severity)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    def get_audit_summary(
        self,
        db: Session,
        tenant_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total = db.query(func.count(AuditLog.id)).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.created_at >= start_date
        ).scalar() or 0
        
        by_action = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.created_at >= start_date
        ).group_by(AuditLog.action).all()
        
        by_severity = db.query(
            AuditLog.severity,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.created_at >= start_date
        ).group_by(AuditLog.severity).all()
        
        security_events = db.query(func.count(AuditLog.id)).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.created_at >= start_date,
            AuditLog.action.in_([
                AuditAction.LOGIN_FAILED,
                AuditAction.GUARDRAIL_TRIGGERED,
                AuditAction.RATE_LIMIT_HIT
            ])
        ).scalar() or 0
        
        return {
            "total_events": total,
            "security_events": security_events,
            "by_action": {a.action.value: a.count for a in by_action},
            "by_severity": {s.severity.value: s.count for s in by_severity}
        }

    def _sanitize_metadata(self, metadata) -> Dict:
        if not metadata:
            return {}
        
        if isinstance(metadata, list):
            return [self._sanitize_value(item) for item in metadata]
        
        if not isinstance(metadata, dict):
            return self._sanitize_value(metadata)
        
        sanitized = {}
        sensitive_keys = [
            'password', 'secret', 'token', 'key', 'credential', 
            'ssn', 'credit_card', 'card_number', 'cvv', 'cvc',
            'account_number', 'routing_number', 'bank_account',
            'pan', 'aadhaar', 'passport', 'driver_license',
            'customer_id', 'user_id', 'client_id', 'member_id',
            'tax_id', 'ein', 'tin', 'national_id',
            'phone', 'mobile', 'email', 'address',
            'dob', 'date_of_birth', 'birth_date',
            'ip', 'ipv4', 'ipv6', 'ip_address'
        ]
        
        for key, value in metadata.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_metadata(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_value(item) for item in value]
            else:
                sanitized[key] = self._sanitize_value(value)
        
        return sanitized

    def _sanitize_value(self, value):
        if isinstance(value, dict):
            return self._sanitize_metadata(value)
        elif isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        elif isinstance(value, str):
            if len(value) > 100:
                return value[:100] + "..."
            return value
        return value

    def export_audit_logs(
        self,
        db: Session,
        tenant_id: int,
        start_date: datetime,
        end_date: datetime,
        sanitize_pii: bool = True
    ) -> List[Dict[str, Any]]:
        logs = db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).order_by(AuditLog.created_at).all()
        
        result = []
        for log in logs:
            metadata = log.metadata_ or {}
            if sanitize_pii:
                metadata = self._sanitize_metadata(metadata)
            
            result.append({
                "id": log.id,
                "timestamp": log.created_at.isoformat(),
                "action": log.action.value,
                "severity": log.severity.value,
                "user_id": log.user_id,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "description": log.description,
                "request_id": log.request_id,
                "ip_address": log.ip_address if not sanitize_pii else self._mask_ip(log.ip_address),
                "metadata": metadata
            })
        
        return result

    def _mask_ip(self, ip_address: str) -> str:
        if not ip_address:
            return None
        
        if ':' in ip_address:
            return "[IPv6_MASKED]"
        
        parts = ip_address.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.xxx.xxx.xxx"
        return "[MASKED]"


audit_service = AuditService()
