-- Smart Login Guardian - Initial Database Schema
-- PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- ORGANIZATIONS & TENANCY
-- =====================================================

CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);

-- =====================================================
-- USERS & AUTHENTICATION
-- =====================================================

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    email_verified BOOLEAN DEFAULT FALSE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    last_login_at TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- =====================================================
-- TENANT MEMBERSHIPS
-- =====================================================

CREATE TABLE tenant_memberships (
    membership_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('super_admin', 'org_admin', 'security_admin', 'security_analyst', 'auditor')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, user_id)
);

CREATE INDEX idx_memberships_tenant ON tenant_memberships(tenant_id);
CREATE INDEX idx_memberships_user ON tenant_memberships(user_id);
CREATE INDEX idx_memberships_role ON tenant_memberships(role);

-- =====================================================
-- API KEYS
-- =====================================================

CREATE TABLE api_keys (
    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL, -- First few characters for identification
    permissions JSONB DEFAULT '[]',
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);

-- =====================================================
-- USER SESSIONS
-- =====================================================

CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(refresh_token_hash);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);

-- =====================================================
-- AUTHENTICATION EVENTS
-- =====================================================

CREATE TABLE authentication_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    external_event_id VARCHAR(255),
    user_identifier VARCHAR(255) NOT NULL,
    ip_address INET NOT NULL,
    country_code VARCHAR(2),
    country_name VARCHAR(100),
    city VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    device_id VARCHAR(255),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    browser_version VARCHAR(50),
    os VARCHAR(100),
    os_version VARCHAR(50),
    user_agent TEXT,
    authentication_method VARCHAR(50) CHECK (authentication_method IN ('password', 'password_mfa', 'oauth', 'saml', 'api_key', 'sso')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'failed', 'blocked')),
    failure_reason VARCHAR(255),
    mfa_status VARCHAR(50) CHECK (mfa_status IN ('not_required', 'passed', 'failed', 'skipped')),
    session_id VARCHAR(255),
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(100),
    raw_event JSONB
);

-- Partitioning by month for performance
CREATE INDEX idx_auth_events_tenant_time ON authentication_events(tenant_id, event_timestamp DESC);
CREATE INDEX idx_auth_events_user_time ON authentication_events(tenant_id, user_identifier, event_timestamp DESC);
CREATE INDEX idx_auth_events_ip ON authentication_events(ip_address);
CREATE INDEX idx_auth_events_status ON authentication_events(tenant_id, status, event_timestamp DESC);
CREATE INDEX idx_auth_events_external_id ON authentication_events(tenant_id, external_event_id);
CREATE INDEX idx_auth_events_timestamp ON authentication_events(event_timestamp DESC);

-- Unique constraint for deduplication
CREATE UNIQUE INDEX idx_auth_events_dedup ON authentication_events(tenant_id, external_event_id) WHERE external_event_id IS NOT NULL;

-- =====================================================
-- RISK ASSESSMENTS
-- =====================================================

CREATE TABLE login_risk_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES authentication_events(event_id) ON DELETE CASCADE,
    risk_score INTEGER NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_level VARCHAR(50) NOT NULL CHECK (risk_level IN ('low', 'moderate', 'elevated', 'high', 'critical')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_risk_tenant_level ON login_risk_assessments(tenant_id, risk_level, created_at DESC);
CREATE INDEX idx_risk_event ON login_risk_assessments(event_id);
CREATE INDEX idx_risk_score ON login_risk_assessments(tenant_id, risk_score DESC);

-- =====================================================
-- RISK SIGNALS
-- =====================================================

CREATE TABLE risk_signals (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES login_risk_assessments(assessment_id) ON DELETE CASCADE,
    signal_type VARCHAR(100) NOT NULL,
    signal_value INTEGER NOT NULL,
    weight INTEGER DEFAULT 1,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_signals_assessment ON risk_signals(assessment_id);
CREATE INDEX idx_signals_type ON risk_signals(signal_type);

-- =====================================================
-- DETECTION RULES
-- =====================================================

CREATE TABLE detection_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    detector_type VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    severity VARCHAR(50) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id)
);

CREATE INDEX idx_rules_tenant ON detection_rules(tenant_id);
CREATE INDEX idx_rules_type ON detection_rules(detector_type);
CREATE INDEX idx_rules_enabled ON detection_rules(enabled);

-- =====================================================
-- DETECTION RESULTS
-- =====================================================

CREATE TABLE detection_results (
    detection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    rule_id UUID REFERENCES detection_rules(rule_id) ON DELETE SET NULL,
    event_id UUID REFERENCES authentication_events(event_id) ON DELETE CASCADE,
    detector_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence DECIMAL(3, 2) CHECK (confidence >= 0 AND confidence <= 1),
    title VARCHAR(255),
    description TEXT,
    evidence JSONB,
    recommended_action VARCHAR(255),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_detections_tenant_severity ON detection_results(tenant_id, severity, detected_at DESC);
CREATE INDEX idx_detections_event ON detection_results(event_id);
CREATE INDEX idx_detections_type ON detection_results(detector_type);
CREATE INDEX idx_detections_time ON detection_results(detected_at DESC);

-- =====================================================
-- SECURITY INCIDENTS
-- =====================================================

CREATE TABLE security_incidents (
    incident_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('new', 'investigating', 'confirmed', 'false_positive', 'resolved', 'closed')),
    assigned_to UUID REFERENCES users(user_id),
    affected_user_identifiers TEXT[],
    source_ip_addresses INET[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(user_id)
);

CREATE INDEX idx_incidents_tenant_status ON security_incidents(tenant_id, status, created_at DESC);
CREATE INDEX idx_incidents_severity ON security_incidents(tenant_id, severity, created_at DESC);
CREATE INDEX idx_incidents_assigned ON security_incidents(assigned_to);
CREATE INDEX idx_incidents_time ON security_incidents(created_at DESC);

-- =====================================================
-- INCIDENT EVENTS (Timeline)
-- =====================================================

CREATE TABLE incident_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES security_incidents(incident_id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id)
);

CREATE INDEX idx_incident_events_incident ON incident_events(incident_id, created_at DESC);
CREATE INDEX idx_incident_events_type ON incident_events(event_type);

-- =====================================================
-- INCIDENT NOTES
-- =====================================================

CREATE TABLE incident_notes (
    note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES security_incidents(incident_id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(user_id),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_incident_notes_incident ON incident_notes(incident_id, created_at DESC);
CREATE INDEX idx_incident_notes_author ON incident_notes(author_id);

-- =====================================================
-- DEVICES
-- =====================================================

CREATE TABLE devices (
    device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    device_fingerprint VARCHAR(255) NOT NULL,
    device_type VARCHAR(50),
    os VARCHAR(100),
    os_version VARCHAR(50),
    browser VARCHAR(100),
    browser_version VARCHAR(50),
    trust_status VARCHAR(50) DEFAULT 'unrecognized' CHECK (trust_status IN ('trusted', 'unrecognized', 'suspicious', 'blocked')),
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    associated_users TEXT[]
);

CREATE UNIQUE INDEX idx_devices_tenant_fingerprint ON devices(tenant_id, device_fingerprint);
CREATE INDEX idx_devices_trust ON devices(tenant_id, trust_status);

-- =====================================================
-- IP INTELLIGENCE
-- =====================================================

CREATE TABLE ip_intelligence (
    ip_address INET PRIMARY KEY,
    reputation_score INTEGER CHECK (reputation_score >= 0 AND reputation_score <= 100),
    is_malicious BOOLEAN DEFAULT FALSE,
    is_vpn BOOLEAN DEFAULT FALSE,
    is_tor BOOLEAN DEFAULT FALSE,
    is_proxy BOOLEAN DEFAULT FALSE,
    is_hosting BOOLEAN DEFAULT FALSE,
    asn INTEGER,
    asn_org VARCHAR(255),
    country_code VARCHAR(2),
    threat_categories TEXT[],
    last_seen TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ip_intel_malicious ON ip_intelligence(is_malicious);
CREATE INDEX idx_ip_intel_vpn ON ip_intelligence(is_vpn);
CREATE INDEX idx_ip_intel_asn ON ip_intelligence(asn);
CREATE INDEX idx_ip_intel_country ON ip_intelligence(country_code);

-- =====================================================
-- INTEGRATIONS
-- =====================================================

CREATE TABLE integrations (
    integration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    integration_type VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    configuration JSONB DEFAULT '{}',
    credentials JSONB, -- Encrypted sensitive data
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_integrations_tenant ON integrations(tenant_id);
CREATE INDEX idx_integrations_type ON integrations(integration_type);
CREATE INDEX idx_integrations_enabled ON integrations(enabled);

-- =====================================================
-- NOTIFICATION CHANNELS
-- =====================================================

CREATE TABLE notification_channels (
    channel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'slack', 'teams', 'webhook', 'in_app')),
    name VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notification_channels_tenant ON notification_channels(tenant_id);
CREATE INDEX idx_notification_channels_type ON notification_channels(channel_type);
CREATE INDEX idx_notification_channels_enabled ON notification_channels(enabled);

-- =====================================================
-- NOTIFICATION HISTORY
-- =====================================================

CREATE TABLE notification_history (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    channel_id UUID REFERENCES notification_channels(channel_id) ON DELETE SET NULL,
    notification_type VARCHAR(100) NOT NULL,
    recipient VARCHAR(255),
    subject VARCHAR(255),
    content TEXT,
    status VARCHAR(50) CHECK (status IN ('pending', 'sent', 'failed', 'retrying')),
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notification_history_tenant ON notification_history(tenant_id, created_at DESC);
CREATE INDEX idx_notification_history_channel ON notification_history(channel_id);
CREATE INDEX idx_notification_history_status ON notification_history(status);

-- =====================================================
-- AUDIT LOGS
-- =====================================================

CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_tenant_time ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- =====================================================
-- AI EXPLANATIONS
-- =====================================================

CREATE TABLE ai_explanations (
    explanation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    event_id UUID REFERENCES authentication_events(event_id) ON DELETE CASCADE,
    incident_id UUID REFERENCES security_incidents(incident_id) ON DELETE CASCADE,
    explanation_type VARCHAR(100),
    executive_summary TEXT,
    technical_explanation TEXT,
    risk_indicators JSONB,
    potential_scenarios JSONB,
    investigation_steps JSONB,
    recommended_remediation JSONB,
    confidence VARCHAR(50) CHECK (confidence IN ('low', 'medium', 'high')),
    model_used VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ai_explanations_tenant ON ai_explanations(tenant_id);
CREATE INDEX idx_ai_explanations_event ON ai_explanations(event_id);
CREATE INDEX idx_ai_explanations_incident ON ai_explanations(incident_id);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_memberships_updated_at BEFORE UPDATE ON tenant_memberships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_detection_rules_updated_at BEFORE UPDATE ON detection_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_security_incidents_updated_at BEFORE UPDATE ON security_incidents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_incident_notes_updated_at BEFORE UPDATE ON incident_notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_integrations_updated_at BEFORE UPDATE ON integrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_channels_updated_at BEFORE UPDATE ON notification_channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- ROW LEVEL SECURITY (Multi-Tenancy)
-- =====================================================

-- Enable RLS on all tenant-specific tables
ALTER TABLE authentication_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_risk_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE detection_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_explanations ENABLE ROW LEVEL SECURITY;

-- Note: RLS policies will be created by application based on current tenant context
-- Example policy (commented out, created dynamically):
-- CREATE POLICY tenant_isolation_policy ON authentication_events
--     USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Create default super admin tenant
INSERT INTO tenants (name, slug, status) VALUES ('System', 'system', 'active');

-- =====================================================
-- VIEWS
-- =====================================================

-- High-risk events view
CREATE VIEW high_risk_events AS
SELECT
    ae.event_id,
    ae.tenant_id,
    ae.user_identifier,
    ae.ip_address,
    ae.country_name,
    ae.city,
    ae.event_timestamp,
    lra.risk_score,
    lra.risk_level,
    ae.status,
    ae.authentication_method
FROM authentication_events ae
JOIN login_risk_assessments lra ON ae.event_id = lra.event_id
WHERE lra.risk_level IN ('high', 'critical')
ORDER BY ae.event_timestamp DESC;

-- Active incidents view
CREATE VIEW active_incidents AS
SELECT
    si.incident_id,
    si.tenant_id,
    si.title,
    si.severity,
    si.status,
    si.assigned_to,
    u.full_name AS assigned_to_name,
    si.created_at,
    si.updated_at,
    (SELECT COUNT(*) FROM incident_notes WHERE incident_id = si.incident_id) AS note_count,
    (SELECT COUNT(*) FROM incident_events WHERE incident_id = si.incident_id) AS event_count
FROM security_incidents si
LEFT JOIN users u ON si.assigned_to = u.user_id
WHERE si.status NOT IN ('resolved', 'closed')
ORDER BY si.severity DESC, si.created_at DESC;

-- Tenant statistics view
CREATE VIEW tenant_statistics AS
SELECT
    t.tenant_id,
    t.name,
    t.slug,
    COUNT(DISTINCT ae.event_id) AS total_events,
    COUNT(DISTINCT ae.user_identifier) AS unique_users,
    COUNT(DISTINCT ae.ip_address) AS unique_ips,
    COUNT(DISTINCT CASE WHEN ae.status = 'failed' THEN ae.event_id END) AS failed_attempts,
    COUNT(DISTINCT CASE WHEN lra.risk_level = 'critical' THEN ae.event_id END) AS critical_events,
    COUNT(DISTINCT si.incident_id) AS total_incidents,
    COUNT(DISTINCT CASE WHEN si.status NOT IN ('resolved', 'closed') THEN si.incident_id END) AS active_incidents
FROM tenants t
LEFT JOIN authentication_events ae ON t.tenant_id = ae.tenant_id
LEFT JOIN login_risk_assessments lra ON ae.event_id = lra.event_id
LEFT JOIN security_incidents si ON t.tenant_id = si.tenant_id
GROUP BY t.tenant_id, t.name, t.slug;

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE tenants IS 'Organizations/customers using the platform';
COMMENT ON TABLE users IS 'Platform users (security analysts, admins)';
COMMENT ON TABLE authentication_events IS 'Ingested authentication events from monitored applications';
COMMENT ON TABLE login_risk_assessments IS 'Risk scores and levels for authentication events';
COMMENT ON TABLE risk_signals IS 'Individual risk factors contributing to overall risk score';
COMMENT ON TABLE detection_results IS 'Threat detections from various detection engines';
COMMENT ON TABLE security_incidents IS 'Security incidents requiring investigation';
COMMENT ON TABLE ip_intelligence IS 'IP reputation and threat intelligence data';
COMMENT ON TABLE ai_explanations IS 'AI-generated security explanations and recommendations';
