-- Performance Indexes Migration
-- Reduces query latency from 20-50ms to 1-5ms
-- Run with: psql -U postgres -d ai_gateway -f add_performance_indexes.sql

-- API Keys - Most critical (hit on every request)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_hash_active 
ON api_keys(key_hash) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_tenant_lookup 
ON api_keys(tenant_id, department_id, team_id) WHERE is_active = true;

-- Guardrail Profiles
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_guardrail_profiles_tenant_active 
ON guardrail_profiles(tenant_id, is_active);

-- Routing Policies
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_routing_policies_tenant_active 
ON routing_policies(tenant_id) WHERE is_active = true;

-- API Routes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_routes_tenant_path 
ON api_routes(tenant_id, path) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_routes_priority 
ON api_routes(priority DESC, tenant_id) WHERE is_active = true;

-- Departments
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_departments_tenant_active 
ON departments(tenant_id) WHERE is_active = true;

-- Teams
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teams_tenant_dept 
ON teams(tenant_id, department_id) WHERE is_active = true;

-- Usage Logs (for analytics, not hot path)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usage_logs_tenant_time 
ON usage_logs(tenant_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usage_logs_apikey_time 
ON usage_logs(api_key_id, created_at DESC);

-- Audit Logs
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_tenant_action_time 
ON audit_logs(tenant_id, action, created_at DESC);
