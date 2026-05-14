CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role_arn VARCHAR(512),
    s3_bucket VARCHAR(255),
    s3_prefix VARCHAR(512) DEFAULT '',
    aws_region VARCHAR(50) DEFAULT 'us-east-1',
    sync_pin_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    service VARCHAR(100) NOT NULL,
    action VARCHAR(255) NOT NULL,
    score INTEGER NOT NULL,
    event_id VARCHAR(100),
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, event_id)
);

CREATE TABLE IF NOT EXISTS daily_scores (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_score INTEGER NOT NULL,
    UNIQUE(user_id, date)
);

CREATE TABLE IF NOT EXISTS processing_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    last_processed_timestamp TIMESTAMP NOT NULL,
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS resource_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    parent_resource_id VARCHAR(255),
    state VARCHAR(100) NOT NULL,
    metadata TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, resource_type, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_user_date ON activity_logs(user_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_scores_user_date ON daily_scores(user_id, date);
CREATE INDEX IF NOT EXISTS idx_resource_state_user ON resource_state(user_id, resource_type, state);
