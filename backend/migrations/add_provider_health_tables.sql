-- Migration: Add Provider Health Tracking Tables
-- Date: 2024-12-04
-- Description: Adds tables for circuit breaker persistence, load balancer metrics, and provider health tracking

-- Provider Health Status Table
CREATE TABLE IF NOT EXISTS provider_health_status (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),
    provider_name VARCHAR(100) NOT NULL,
    
    -- Circuit Breaker State
    circuit_state VARCHAR(20) DEFAULT 'closed',
    failure_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    consecutive_failures INTEGER DEFAULT 0,
    consecutive_successes INTEGER DEFAULT 0,
    
    last_failure_at TIMESTAMP,
    last_success_at TIMESTAMP,
    circuit_opened_at TIMESTAMP,
    
    -- Circuit Breaker Configuration
    failure_threshold INTEGER DEFAULT 5,
    success_threshold INTEGER DEFAULT 2,
    timeout_seconds INTEGER DEFAULT 30,
    window_seconds INTEGER DEFAULT 60,
    
    -- Health Metrics
    is_healthy BOOLEAN DEFAULT TRUE,
    health_check_failures INTEGER DEFAULT 0,
    last_health_check_at TIMESTAMP,
    
    -- Load Balancer Metrics
    active_requests INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,
    avg_latency_ms FLOAT DEFAULT 0.0,
    
    -- Provider Metadata
    endpoint_url VARCHAR(500),
    provider_config_id INTEGER REFERENCES provider_configs_v2(id),
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_provider_health_tenant ON provider_health_status(tenant_id);
CREATE INDEX IF NOT EXISTS idx_provider_health_name ON provider_health_status(provider_name);
CREATE INDEX IF NOT EXISTS idx_provider_health_created ON provider_health_status(created_at);

-- Provider Health History Table
CREATE TABLE IF NOT EXISTS provider_health_history (
    id SERIAL PRIMARY KEY,
    provider_status_id INTEGER REFERENCES provider_health_status(id) ON DELETE CASCADE,
    tenant_id INTEGER REFERENCES tenants(id),
    provider_name VARCHAR(100) NOT NULL,
    
    event_type VARCHAR(50) NOT NULL,
    event_details JSONB DEFAULT '{}',
    
    circuit_state_before VARCHAR(20),
    circuit_state_after VARCHAR(20),
    
    failure_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    latency_ms FLOAT,
    
    error_message TEXT,
    error_category VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_provider_history_status ON provider_health_history(provider_status_id);
CREATE INDEX IF NOT EXISTS idx_provider_history_tenant ON provider_health_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_provider_history_name ON provider_health_history(provider_name);
CREATE INDEX IF NOT EXISTS idx_provider_history_type ON provider_health_history(event_type);
CREATE INDEX IF NOT EXISTS idx_provider_history_created ON provider_health_history(created_at);

-- Load Balancer Metrics Table
CREATE TABLE IF NOT EXISTS load_balancer_metrics (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),
    
    group_name VARCHAR(100) NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    
    strategy VARCHAR(50) DEFAULT 'weighted_round_robin',
    weight INTEGER DEFAULT 1,
    
    time_bucket TIMESTAMP NOT NULL,
    bucket_type VARCHAR(20) DEFAULT 'hourly',
    
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    
    total_latency_ms FLOAT DEFAULT 0.0,
    avg_latency_ms FLOAT DEFAULT 0.0,
    min_latency_ms FLOAT,
    max_latency_ms FLOAT,
    
    requests_percentage FLOAT DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lb_metrics_tenant ON load_balancer_metrics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_lb_metrics_group ON load_balancer_metrics(group_name);
CREATE INDEX IF NOT EXISTS idx_lb_metrics_provider ON load_balancer_metrics(provider_name);
CREATE INDEX IF NOT EXISTS idx_lb_metrics_bucket ON load_balancer_metrics(time_bucket);

-- Circuit Breaker Events Table
CREATE TABLE IF NOT EXISTS circuit_breaker_events (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),
    provider_name VARCHAR(100) NOT NULL,
    
    event_type VARCHAR(50) NOT NULL,
    state_before VARCHAR(20) NOT NULL,
    state_after VARCHAR(20) NOT NULL,
    
    failure_count INTEGER DEFAULT 0,
    consecutive_failures INTEGER DEFAULT 0,
    
    trigger_reason VARCHAR(255),
    triggered_by VARCHAR(100),
    duration_in_state_seconds INTEGER,
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cb_events_tenant ON circuit_breaker_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cb_events_provider ON circuit_breaker_events(provider_name);
CREATE INDEX IF NOT EXISTS idx_cb_events_created ON circuit_breaker_events(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_provider_health_status_updated_at BEFORE UPDATE ON provider_health_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_load_balancer_metrics_updated_at BEFORE UPDATE ON load_balancer_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Migration completed
