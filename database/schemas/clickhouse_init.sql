-- ClickHouse Analytics Database Schema
-- Smart Login Guardian - Authentication Events Analytics

-- =====================================================
-- Authentication Events (Analytics / Cold Storage)
-- =====================================================

CREATE DATABASE IF NOT EXISTS smart_login_guardian_analytics;

USE smart_login_guardian_analytics;

CREATE TABLE IF NOT EXISTS auth_events_analytics (
    event_id UUID,
    tenant_id UUID,
    user_identifier String,
    ip_address IPv4,
    country_code FixedString(2),
    country_name String,
    city String,
    latitude Decimal(10, 8),
    longitude Decimal(11, 8),
    device_id String,
    device_type String,
    browser String,
    browser_version String,
    os String,
    os_version String,
    auth_method String,
    status String,
    failure_reason String,
    mfa_status String,
    risk_score UInt8,
    risk_level String,
    event_timestamp DateTime('UTC'),
    ingested_at DateTime('UTC') DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_timestamp)
ORDER BY (tenant_id, event_timestamp, user_identifier)
TTL event_timestamp + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- =====================================================
-- Risk Assessments Analytics
-- =====================================================

CREATE TABLE IF NOT EXISTS risk_assessments_analytics (
    assessment_id UUID,
    tenant_id UUID,
    event_id UUID,
    risk_score UInt8,
    risk_level String,
    signal_count UInt16,
    created_at DateTime('UTC')
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (tenant_id, created_at, risk_level)
TTL created_at + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- =====================================================
-- Detection Results Analytics
-- =====================================================

CREATE TABLE IF NOT EXISTS detection_results_analytics (
    detection_id UUID,
    tenant_id UUID,
    event_id UUID,
    detector_type String,
    severity String,
    confidence Decimal(3, 2),
    title String,
    detected_at DateTime('UTC')
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(detected_at)
ORDER BY (tenant_id, severity, detected_at)
TTL detected_at + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- =====================================================
-- Materialized Views for Aggregations
-- =====================================================

-- Hourly authentication events summary
CREATE MATERIALIZED VIEW IF NOT EXISTS auth_events_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (tenant_id, hour, status, risk_level)
AS SELECT
    tenant_id,
    toStartOfHour(event_timestamp) AS hour,
    status,
    risk_level,
    country_code,
    count() AS event_count,
    uniq(user_identifier) AS unique_users,
    uniq(ip_address) AS unique_ips,
    uniq(device_id) AS unique_devices
FROM auth_events_analytics
GROUP BY tenant_id, hour, status, risk_level, country_code;

-- Daily authentication events summary
CREATE MATERIALIZED VIEW IF NOT EXISTS auth_events_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (tenant_id, day, status)
AS SELECT
    tenant_id,
    toDate(event_timestamp) AS day,
    status,
    risk_level,
    auth_method,
    count() AS event_count,
    uniq(user_identifier) AS unique_users,
    uniq(ip_address) AS unique_ips,
    uniq(country_code) AS unique_countries
FROM auth_events_analytics
GROUP BY tenant_id, day, status, risk_level, auth_method;

-- Geographic distribution
CREATE MATERIALIZED VIEW IF NOT EXISTS auth_events_by_country
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (tenant_id, day, country_code)
AS SELECT
    tenant_id,
    toDate(event_timestamp) AS day,
    country_code,
    country_name,
    count() AS event_count,
    countIf(status = 'failed') AS failed_count,
    countIf(risk_level = 'critical') AS critical_count,
    uniq(user_identifier) AS unique_users
FROM auth_events_analytics
GROUP BY tenant_id, day, country_code, country_name;

-- Risk distribution
CREATE MATERIALIZED VIEW IF NOT EXISTS risk_distribution
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (tenant_id, hour, risk_level)
AS SELECT
    tenant_id,
    toStartOfHour(event_timestamp) AS hour,
    risk_level,
    count() AS event_count
FROM auth_events_analytics
WHERE risk_level != ''
GROUP BY tenant_id, hour, risk_level;

-- Top suspicious IPs
CREATE MATERIALIZED VIEW IF NOT EXISTS top_suspicious_ips
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (tenant_id, day, ip_address)
AS SELECT
    tenant_id,
    toDate(event_timestamp) AS day,
    ip_address,
    countState() AS event_count,
    countIfState(status = 'failed') AS failed_count,
    countIfState(risk_level IN ('high', 'critical')) AS high_risk_count,
    uniqState(user_identifier) AS unique_users
FROM auth_events_analytics
GROUP BY tenant_id, day, ip_address;

-- =====================================================
-- Indexes for Query Optimization
-- =====================================================

-- Create indexes for common queries
ALTER TABLE auth_events_analytics ADD INDEX idx_user_identifier user_identifier TYPE bloom_filter GRANULARITY 1;
ALTER TABLE auth_events_analytics ADD INDEX idx_ip_address ip_address TYPE bloom_filter GRANULARITY 1;
ALTER TABLE auth_events_analytics ADD INDEX idx_risk_level risk_level TYPE set(0) GRANULARITY 1;

-- =====================================================
-- Sample Queries (Commented Out - For Reference)
-- =====================================================

/*
-- Get hourly login trends for a tenant
SELECT
    hour,
    status,
    event_count,
    unique_users
FROM auth_events_hourly
WHERE tenant_id = 'your-tenant-id'
  AND hour >= now() - INTERVAL 24 HOUR
ORDER BY hour DESC;

-- Get geographic distribution
SELECT
    country_name,
    event_count,
    failed_count,
    critical_count
FROM auth_events_by_country
WHERE tenant_id = 'your-tenant-id'
  AND day = today()
ORDER BY event_count DESC
LIMIT 20;

-- Get risk distribution
SELECT
    risk_level,
    sum(event_count) AS total
FROM risk_distribution
WHERE tenant_id = 'your-tenant-id'
  AND hour >= now() - INTERVAL 24 HOUR
GROUP BY risk_level
ORDER BY total DESC;

-- Get top suspicious IPs
SELECT
    ip_address,
    countMerge(event_count) AS total_events,
    countMerge(failed_count) AS failed_attempts,
    countMerge(high_risk_count) AS high_risk_events,
    uniqMerge(unique_users) AS users_count
FROM top_suspicious_ips
WHERE tenant_id = 'your-tenant-id'
  AND day >= today() - INTERVAL 7
GROUP BY ip_address
HAVING failed_attempts > 5
ORDER BY high_risk_events DESC
LIMIT 100;

-- Search authentication events
SELECT
    event_id,
    user_identifier,
    ip_address,
    country_name,
    city,
    status,
    risk_score,
    risk_level,
    event_timestamp
FROM auth_events_analytics
WHERE tenant_id = 'your-tenant-id'
  AND event_timestamp >= now() - INTERVAL 7 DAY
  AND (
    user_identifier LIKE '%search_term%'
    OR ip_address = IPv4StringToNum('192.168.1.1')
  )
ORDER BY event_timestamp DESC
LIMIT 100;
*/
