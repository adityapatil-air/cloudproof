CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role_arn VARCHAR(512),
    credential_type VARCHAR(20) CHECK(credential_type IN ('access_key', 'role_arn')),
    aws_access_key_encrypted TEXT,
    aws_secret_key_encrypted TEXT,
    cloudtrail_bucket VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    service VARCHAR(100) NOT NULL,
    action VARCHAR(255) NOT NULL,
    score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

CREATE INDEX idx_activity_logs_user_date ON activity_logs(user_id, date);
CREATE INDEX idx_daily_scores_user_date ON daily_scores(user_id, date);

CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
