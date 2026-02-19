-- Auth Service Database Schema
-- PostgreSQL SQL Schema Definition

-- Create UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table: Core user information
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(32) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,

    CONSTRAINT users_username_length CHECK (LENGTH(username) >= 3 AND LENGTH(username) <= 32),
    CONSTRAINT users_email_length CHECK (LENGTH(email) >= 5 AND LENGTH(email) <= 255),
    CONSTRAINT users_valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Create indexes for users table
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_users_locked_until ON users(locked_until) WHERE locked_until IS NOT NULL;


-- Login Attempts table: Track login attempts for rate limiting
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    username VARCHAR(32) NOT NULL,
    email VARCHAR(255),
    success BOOLEAN NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    error_reason VARCHAR(100),
    attempt_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT login_attempts_time_range CHECK (attempt_at >= CURRENT_TIMESTAMP - INTERVAL '30 days')
);

-- Create indexes for login_attempts table
CREATE INDEX idx_login_attempts_user_id ON login_attempts(user_id);
CREATE INDEX idx_login_attempts_username ON login_attempts(username);
CREATE INDEX idx_login_attempts_attempt_at ON login_attempts(attempt_at DESC);
CREATE INDEX idx_login_attempts_success ON login_attempts(success) WHERE success = FALSE;
CREATE INDEX idx_login_attempts_recent ON login_attempts(username, attempt_at DESC) WHERE attempt_at >= CURRENT_TIMESTAMP - INTERVAL '15 minutes';


-- Refresh Tokens table: For token refresh mechanism (future enhancement)
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_jti UUID NOT NULL DEFAULT uuid_generate_v4(),
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,

    CONSTRAINT refresh_tokens_future_expiry CHECK (expires_at > issued_at)
);

-- Create indexes for refresh_tokens table
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_jti ON refresh_tokens(token_jti) WHERE revoked_at IS NULL;
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at) WHERE revoked_at IS NULL;
CREATE INDEX idx_refresh_tokens_revoked ON refresh_tokens(revoked_at) WHERE revoked_at IS NOT NULL;


-- Audit Log table: For security audit trail (future enhancement)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(50),
    status VARCHAR(20),
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id UUID,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit_logs table
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_request_id ON audit_logs(request_id) WHERE request_id IS NOT NULL;


-- Trigger to update users.updated_at on modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- View for users with stats (future use)
CREATE VIEW user_stats AS
SELECT
    u.id,
    u.username,
    u.email,
    u.created_at,
    u.last_login_at,
    COUNT(CASE WHEN la.success = FALSE AND la.attempt_at >= CURRENT_TIMESTAMP - INTERVAL '15 minutes' THEN 1 END) as recent_failed_attempts,
    COUNT(CASE WHEN la.success = TRUE THEN 1 END) as total_successful_logins,
    COUNT(CASE WHEN la.success = FALSE THEN 1 END) as total_failed_logins
FROM users u
LEFT JOIN login_attempts la ON u.id = la.user_id
GROUP BY u.id, u.username, u.email, u.created_at, u.last_login_at;


-- Data cleanup procedure (optional, for maintenance)
CREATE OR REPLACE PROCEDURE cleanup_old_login_attempts(days_back INTEGER DEFAULT 30)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM login_attempts
    WHERE attempt_at < CURRENT_TIMESTAMP - (days_back || ' days')::INTERVAL;

    RAISE NOTICE 'Cleaned up login attempts older than % days', days_back;
END;
$$;

CREATE OR REPLACE PROCEDURE cleanup_expired_refresh_tokens()
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM refresh_tokens
    WHERE expires_at < CURRENT_TIMESTAMP;

    RAISE NOTICE 'Cleaned up expired refresh tokens';
END;
$$;


-- ========== Data Dictionary ==========
/*

TABLE: users
- id: Primary key, auto-incrementing integer
- username: Unique username, 3-32 characters, alphanumeric + underscore
- email: Unique email address, validated with regex
- password_hash: Bcrypt hashed password (60 characters)
- is_active: Boolean flag, TRUE by default, FALSE when user is disabled
- is_locked: Boolean flag, TRUE when account is locked due to failed attempts
- failed_login_attempts: Integer counter for rate limiting (0-5)
- locked_until: TIMESTAMP when account will be unlocked (initially NULL)
- created_at: User creation timestamp, DEFAULT CURRENT_TIMESTAMP
- updated_at: Last modification timestamp, updated by trigger
- last_login_at: Timestamp of last successful login (initially NULL)

TABLE: login_attempts
- id: Primary key, auto-incrementing integer
- user_id: Foreign key to users table (nullable, in case user is deleted)
- username: Username at time of attempt (for logging purposes)
- email: Email at time of attempt (for logging purposes)
- success: Boolean, TRUE if login succeeded, FALSE if failed
- ip_address: IPv4 or IPv6 address of client
- user_agent: User agent string from HTTP header
- error_reason: Reason for failed attempt (e.g., 'wrong_password', 'user_not_found')
- attempt_at: Timestamp of attempt, DEFAULT CURRENT_TIMESTAMP
Purpose: Rate limiting, failed attempt tracking, audit trail

TABLE: refresh_tokens
- id: Primary key, auto-incrementing integer
- user_id: Foreign key to users table, cascade delete
- token_jti: Unique UUID for token identification (JWT ID)
- token_hash: SHA256 hash of actual token (for storage security)
- issued_at: Timestamp when token was issued
- expires_at: Timestamp when token expires
- revoked_at: Timestamp when token was manually revoked (NULL if active)
- ip_address: IPv4 or IPv6 address of client that received token
- user_agent: User agent string when token was issued
Purpose: Token refresh mechanism, token blacklisting

TABLE: audit_logs
- id: Primary key, auto-incrementing integer
- user_id: Foreign key to users table (nullable if action not related to user)
- action: Type of action (e.g., 'REGISTER', 'LOGIN', 'PASSWORD_RESET', 'ACCOUNT_LOCKED')
- resource_type: Type of resource affected (e.g., 'USER', 'TOKEN')
- resource_id: ID of resource affected
- status: Result of action ('SUCCESS', 'FAILURE', 'PENDING')
- ip_address: IPv4 or IPv6 address of client
- user_agent: User agent string from HTTP header
- request_id: UUID for correlating multiple log entries
- details: JSONB for flexible additional information
- created_at: Timestamp of audit log entry
Purpose: Security audit trail, compliance logging, incident investigation

*/
