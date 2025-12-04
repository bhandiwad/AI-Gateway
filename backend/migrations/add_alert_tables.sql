-- Migration: Add Alert and Notification Tables
-- Date: 2024-12-04
-- Description: Adds tables for alert configuration and notification delivery

-- Alert Configurations
CREATE TABLE IF NOT EXISTS alert_configs (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    is_active BOOLEAN DEFAULT TRUE,
    
    alert_type VARCHAR(50) NOT NULL,
    conditions JSONB DEFAULT '{}',
    channels JSONB DEFAULT '[]',
    channel_config JSONB DEFAULT '{}',
    
    cooldown_minutes INTEGER DEFAULT 15,
    max_alerts_per_hour INTEGER DEFAULT 10,
    severity VARCHAR(20) DEFAULT 'warning',
    group_similar BOOLEAN DEFAULT TRUE,
    
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_configs_tenant ON alert_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alert_configs_type ON alert_configs(alert_type);

-- Alert Notifications
CREATE TABLE IF NOT EXISTS alert_notifications (
    id SERIAL PRIMARY KEY,
    alert_config_id INTEGER NOT NULL REFERENCES alert_configs(id) ON DELETE CASCADE,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    
    channels_sent JSONB DEFAULT '[]',
    delivery_status JSONB DEFAULT '{}',
    
    is_read BOOLEAN DEFAULT FALSE,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    
    group_key VARCHAR(255),
    is_grouped BOOLEAN DEFAULT FALSE,
    similar_count INTEGER DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_notifications_config ON alert_notifications(alert_config_id);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_tenant ON alert_notifications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_type ON alert_notifications(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_created ON alert_notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_group ON alert_notifications(group_key);

-- Alert Throttling
CREATE TABLE IF NOT EXISTS alert_throttles (
    id SERIAL PRIMARY KEY,
    alert_config_id INTEGER NOT NULL REFERENCES alert_configs(id) ON DELETE CASCADE,
    
    throttle_key VARCHAR(255) NOT NULL,
    
    last_sent_at TIMESTAMP NOT NULL,
    sent_count_this_hour INTEGER DEFAULT 1,
    hour_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_allowed_at TIMESTAMP NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_throttles_config ON alert_throttles(alert_config_id);
CREATE INDEX IF NOT EXISTS idx_alert_throttles_key ON alert_throttles(throttle_key);

-- User Notification Preferences
CREATE TABLE IF NOT EXISTS notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    
    email_enabled BOOLEAN DEFAULT TRUE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    slack_enabled BOOLEAN DEFAULT FALSE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    
    email_address VARCHAR(255),
    phone_number VARCHAR(50),
    slack_user_id VARCHAR(100),
    
    alert_type_preferences JSONB DEFAULT '{}',
    
    quiet_hours_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),
    quiet_hours_timezone VARCHAR(50) DEFAULT 'UTC',
    
    enable_digest BOOLEAN DEFAULT FALSE,
    digest_frequency VARCHAR(20) DEFAULT 'daily',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notification_prefs_user ON notification_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_prefs_tenant ON notification_preferences(tenant_id);

-- Triggers for updated_at
CREATE TRIGGER update_alert_configs_updated_at BEFORE UPDATE ON alert_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alert_throttles_updated_at BEFORE UPDATE ON alert_throttles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_prefs_updated_at BEFORE UPDATE ON notification_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Migration completed
