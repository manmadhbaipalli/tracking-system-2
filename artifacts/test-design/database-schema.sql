-- FastAPI Authentication Service Database Schema
-- PostgreSQL 13+
-- Date: 2026-02-19

-- ============================================================================
-- USERS TABLE
-- ============================================================================
-- Stores user account information with authentication details

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,

    -- User Identification
    username VARCHAR(32) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,

    -- Security
    password_hash VARCHAR(255) NOT NULL,

    -- Account Status
    is_locked BOOLEAN DEFAULT FALSE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL,

    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,

    -- Constraints
    CONSTRAINT username_length CHECK (char_length(username) >= 3 AND char_length(username) <= 32),
    CONSTRAINT email_format CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Indexes for frequently queried columns
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_locked ON users(is_locked);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================================
-- LOGIN_ATTEMPTS TABLE
-- ============================================================================
-- Tracks login attempts (success and failure) for auditing and rate limiting

CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,

    -- Foreign Key
    user_id INTEGER NOT NULL,

    -- Attempt Details
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),

    -- Foreign Key Constraint
    CONSTRAINT fk_login_attempts_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for query performance
CREATE INDEX idx_login_attempts_user_id ON login_attempts(user_id);
CREATE INDEX idx_login_attempts_timestamp ON login_attempts(attempted_at);
CREATE INDEX idx_login_attempts_user_timestamp ON login_attempts(user_id, attempted_at);
CREATE INDEX idx_login_attempts_success ON login_attempts(success);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
CREATE TRIGGER trigger_update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS (OPTIONAL)
-- ============================================================================

-- Recent failed login attempts (for rate limiting queries)
CREATE OR REPLACE VIEW recent_failed_attempts AS
SELECT
    user_id,
    COUNT(*) as attempt_count,
    MAX(attempted_at) as last_attempt,
    MIN(attempted_at) as first_attempt
FROM login_attempts
WHERE
    success = FALSE
    AND attempted_at > CURRENT_TIMESTAMP - INTERVAL '15 minutes'
GROUP BY user_id;

-- User login statistics
CREATE OR REPLACE VIEW user_login_stats AS
SELECT
    u.id,
    u.username,
    u.email,
    COUNT(CASE WHEN la.success = TRUE THEN 1 END) as successful_logins,
    COUNT(CASE WHEN la.success = FALSE THEN 1 END) as failed_logins,
    MAX(CASE WHEN la.success = TRUE THEN la.attempted_at END) as last_successful_login,
    MAX(CASE WHEN la.success = FALSE THEN la.attempted_at END) as last_failed_login
FROM users u
LEFT JOIN login_attempts la ON u.id = la.user_id
GROUP BY u.id, u.username, u.email;

-- ============================================================================
-- NOTES
-- ============================================================================
--
-- 1. Password Hash: Stored as bcrypt hash with cost 12 (~60 chars)
--
-- 2. Account Locking:
--    - is_locked: boolean flag indicating if account is locked
--    - locked_until: timestamp when lock expires
--    - failed_login_attempts: counter of failed attempts
--
-- 3. Rate Limiting:
--    - Check login_attempts table for attempts in last 15 minutes
--    - Lock account after 5 failed attempts
--    - Lock expires after 30 minutes
--
-- 4. Indexes: Created on frequently queried columns for performance
--    - username, email for lookups
--    - timestamp for time-range queries
--    - is_locked for account status checks
--
-- 5. Audit Trail:
--    - created_at: when user registered
--    - updated_at: when profile was last modified
--    - last_login_at: when user last logged in successfully
--    - login_attempts: full history of all attempts
--
-- 6. Foreign Keys: ON DELETE CASCADE ensures login attempts deleted with user
--
-- 7. Constraints:
--    - username: 3-32 characters (enforced at app level too)
--    - email: basic format validation (enforced at app level)
--    - Both username and email are globally unique
--
-- 8. Performance Considerations:
--    - Compound index on (user_id, attempted_at) for efficient rate limiting queries
--    - Timestamp index for cleanup/archival of old login attempts
--    - is_locked index for quick account status lookups
--
-- 9. Future Enhancements:
--    - Refresh tokens table for extended sessions
--    - Password history table for preventing reuse
--    - Device/session table for device management
--    - Audit log table for compliance
--    - Email verification table for email validation
--
