"""
Alert Service

Handles alert triggering, throttling, and notification delivery across multiple channels.
"""

import logging
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.app.db.models.alerts import (
    AlertConfig, AlertNotification, AlertThrottle, NotificationPreference,
    AlertType, AlertChannel, AlertSeverity
)

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing and delivering alerts."""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def trigger_alert(
        self,
        db: Session,
        tenant_id: int,
        alert_type: AlertType,
        title: str,
        message: str,
        context: Dict[str, Any],
        severity: AlertSeverity = AlertSeverity.WARNING
    ) -> Optional[AlertNotification]:
        """
        Trigger an alert if conditions are met and not throttled.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            alert_type: Type of alert
            title: Alert title
            message: Alert message
            context: Additional context data
            severity: Alert severity
            
        Returns:
            AlertNotification if sent, None if throttled
        """
        # Find matching alert configs
        configs = db.query(AlertConfig).filter(
            and_(
                AlertConfig.tenant_id == tenant_id,
                AlertConfig.alert_type == alert_type,
                AlertConfig.is_active == True
            )
        ).all()
        
        if not configs:
            logger.debug(f"No alert configs found for {alert_type} in tenant {tenant_id}")
            return None
        
        notifications_sent = []
        
        for config in configs:
            # Check if conditions match
            if not self._check_conditions(config, context):
                continue
            
            # Check throttling
            if self._is_throttled(db, config, context):
                logger.info(f"Alert throttled: {alert_type} for tenant {tenant_id}")
                continue
            
            # Create notification
            notification = await self._create_and_send_notification(
                db, config, title, message, context, severity
            )
            
            if notification:
                notifications_sent.append(notification)
                # Update throttle
                self._update_throttle(db, config, context)
        
        return notifications_sent[0] if notifications_sent else None
    
    def _check_conditions(self, config: AlertConfig, context: Dict[str, Any]) -> bool:
        """Check if alert conditions are met."""
        conditions = config.conditions or {}
        
        # Check threshold conditions
        if "threshold" in conditions:
            threshold = conditions["threshold"]
            current_value = context.get("current_value", 0)
            limit_value = context.get("limit_value", 0)
            
            if limit_value > 0:
                percentage = current_value / limit_value
                if percentage < threshold:
                    return False
        
        # Check provider filter
        if "provider_names" in conditions:
            provider = context.get("provider_name")
            if provider and provider not in conditions["provider_names"]:
                return False
        
        # Check minimum consecutive failures
        if "min_consecutive_failures" in conditions:
            failures = context.get("consecutive_failures", 0)
            if failures < conditions["min_consecutive_failures"]:
                return False
        
        # Check latency threshold
        if "latency_ms" in conditions:
            latency = context.get("latency_ms", 0)
            if latency < conditions["latency_ms"]:
                return False
        
        return True
    
    def _is_throttled(
        self,
        db: Session,
        config: AlertConfig,
        context: Dict[str, Any]
    ) -> bool:
        """Check if alert should be throttled."""
        throttle_key = self._get_throttle_key(config.alert_type, context)
        
        throttle = db.query(AlertThrottle).filter(
            and_(
                AlertThrottle.alert_config_id == config.id,
                AlertThrottle.throttle_key == throttle_key
            )
        ).first()
        
        if not throttle:
            return False
        
        now = datetime.utcnow()
        
        # Check cooldown
        if now < throttle.next_allowed_at:
            return True
        
        # Check hourly limit
        if throttle.hour_started_at and (now - throttle.hour_started_at).seconds < 3600:
            if throttle.sent_count_this_hour >= config.max_alerts_per_hour:
                return True
        
        return False
    
    def _update_throttle(
        self,
        db: Session,
        config: AlertConfig,
        context: Dict[str, Any]
    ):
        """Update throttle record after sending alert."""
        throttle_key = self._get_throttle_key(config.alert_type, context)
        now = datetime.utcnow()
        
        throttle = db.query(AlertThrottle).filter(
            and_(
                AlertThrottle.alert_config_id == config.id,
                AlertThrottle.throttle_key == throttle_key
            )
        ).first()
        
        if throttle:
            # Reset hourly counter if hour passed
            if throttle.hour_started_at and (now - throttle.hour_started_at).seconds >= 3600:
                throttle.sent_count_this_hour = 1
                throttle.hour_started_at = now
            else:
                throttle.sent_count_this_hour += 1
            
            throttle.last_sent_at = now
            throttle.next_allowed_at = now + timedelta(minutes=config.cooldown_minutes)
        else:
            # Create new throttle
            throttle = AlertThrottle(
                alert_config_id=config.id,
                throttle_key=throttle_key,
                last_sent_at=now,
                sent_count_this_hour=1,
                hour_started_at=now,
                next_allowed_at=now + timedelta(minutes=config.cooldown_minutes)
            )
            db.add(throttle)
        
        db.commit()
    
    def _get_throttle_key(self, alert_type: AlertType, context: Dict[str, Any]) -> str:
        """Generate unique throttle key for this alert."""
        provider = context.get("provider_name", "")
        return f"{alert_type.value}:{provider}"
    
    async def _create_and_send_notification(
        self,
        db: Session,
        config: AlertConfig,
        title: str,
        message: str,
        context: Dict[str, Any],
        severity: AlertSeverity
    ) -> Optional[AlertNotification]:
        """Create notification and send to all configured channels."""
        
        # Create notification record
        notification = AlertNotification(
            alert_config_id=config.id,
            tenant_id=config.tenant_id,
            alert_type=config.alert_type,
            severity=severity,
            title=title,
            message=message,
            context=context,
            group_key=self._get_throttle_key(config.alert_type, context) if config.group_similar else None,
            is_grouped=config.group_similar
        )
        
        db.add(notification)
        db.flush()  # Get notification ID
        
        # Send to configured channels
        delivery_status = {}
        channels_sent = []
        
        for channel in config.channels:
            try:
                if channel == AlertChannel.EMAIL.value:
                    success = await self._send_email(config, notification)
                elif channel == AlertChannel.SLACK.value:
                    success = await self._send_slack(config, notification)
                elif channel == AlertChannel.WEBHOOK.value:
                    success = await self._send_webhook(config, notification)
                elif channel == AlertChannel.IN_APP.value:
                    success = True  # Always succeeds (just stored in DB)
                else:
                    success = False
                
                if success:
                    channels_sent.append(channel)
                    delivery_status[channel] = {
                        "status": "sent",
                        "sent_at": datetime.utcnow().isoformat()
                    }
                else:
                    delivery_status[channel] = {
                        "status": "failed",
                        "error": "Delivery failed"
                    }
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
                delivery_status[channel] = {
                    "status": "error",
                    "error": str(e)
                }
        
        notification.channels_sent = channels_sent
        notification.delivery_status = delivery_status
        
        db.commit()
        db.refresh(notification)
        
        return notification
    
    async def _send_email(self, config: AlertConfig, notification: AlertNotification) -> bool:
        """Send email notification."""
        email_config = config.channel_config.get("email", {})
        recipients = email_config.get("recipients", [])
        
        if not recipients:
            logger.warning("No email recipients configured")
            return False
        
        # TODO: Integrate with email service (SendGrid, SES, SMTP)
        logger.info(f"Email sent to {recipients}: {notification.title}")
        return True
    
    async def _send_slack(self, config: AlertConfig, notification: AlertNotification) -> bool:
        """Send Slack notification."""
        slack_config = config.channel_config.get("slack", {})
        webhook_url = slack_config.get("webhook_url")
        
        if not webhook_url:
            logger.warning("No Slack webhook URL configured")
            return False
        
        # Format message for Slack
        color = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9900",
            AlertSeverity.ERROR: "#ff0000",
            AlertSeverity.CRITICAL: "#8b0000"
        }.get(notification.severity, "#cccccc")
        
        payload = {
            "attachments": [{
                "color": color,
                "title": notification.title,
                "text": notification.message,
                "fields": [
                    {"title": k.replace("_", " ").title(), "value": str(v), "short": True}
                    for k, v in notification.context.items()
                ],
                "footer": "AI Gateway Alerts",
                "ts": int(datetime.utcnow().timestamp())
            }]
        }
        
        try:
            response = await self.http_client.post(webhook_url, json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack webhook failed: {e}")
            return False
    
    async def _send_webhook(self, config: AlertConfig, notification: AlertNotification) -> bool:
        """Send webhook notification."""
        webhook_config = config.channel_config.get("webhook", {})
        url = webhook_config.get("url")
        
        if not url:
            logger.warning("No webhook URL configured")
            return False
        
        headers = webhook_config.get("headers", {})
        headers["Content-Type"] = "application/json"
        
        payload = {
            "alert_type": notification.alert_type.value,
            "severity": notification.severity.value,
            "title": notification.title,
            "message": notification.message,
            "context": notification.context,
            "timestamp": notification.created_at.isoformat()
        }
        
        try:
            response = await self.http_client.post(url, json=payload, headers=headers)
            return response.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"Webhook failed: {e}")
            return False
    
    def get_unread_notifications(
        self,
        db: Session,
        tenant_id: int,
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> List[AlertNotification]:
        """Get unread in-app notifications."""
        query = db.query(AlertNotification).filter(
            and_(
                AlertNotification.tenant_id == tenant_id,
                AlertNotification.is_read == False,
                AlertNotification.channels_sent.contains(["in_app"])
            )
        ).order_by(AlertNotification.created_at.desc())
        
        return query.limit(limit).all()
    
    def mark_as_read(self, db: Session, notification_id: int, user_id: int):
        """Mark notification as read."""
        notification = db.query(AlertNotification).filter(
            AlertNotification.id == notification_id
        ).first()
        
        if notification:
            notification.is_read = True
            db.commit()
    
    def acknowledge_alert(self, db: Session, notification_id: int, user_id: int):
        """Acknowledge an alert."""
        notification = db.query(AlertNotification).filter(
            AlertNotification.id == notification_id
        ).first()
        
        if notification:
            notification.is_acknowledged = True
            notification.acknowledged_by = user_id
            notification.acknowledged_at = datetime.utcnow()
            db.commit()


# Global alert service instance
alert_service = AlertService()
