# Database Schema Design

## Overview

The authentication service uses a PostgreSQL database (with SQLite support for development) with a focus on security, performance, and maintainability. The schema is designed to support user management, session tracking, and audit trails.

## Tables

### Users Table

The primary table for storing user account information.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Field Specifications

- **id**: UUID primary key for security and uniqueness across distributed systems
- **email**: User's email address, unique constraint for login identification
- **username**: Display name, unique constraint, alphanumeric + underscore only
- **hashed_password**: BCrypt hashed password, never store plaintext
- **is_active**: Soft delete flag, allows account deactivation without data loss
- **is_superuser**: Admin flag for future authorization features
- **created_at**: Account creation timestamp with timezone
- **updated_at**: Last modification timestamp, updated via triggers

#### Constraints

```sql
-- Email format validation
ALTER TABLE users ADD CONSTRAINT users_email_format
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Username format validation (3-50 chars, alphanumeric + underscore)
ALTER TABLE users ADD CONSTRAINT users_username_format
    CHECK (username ~* '^[A-Za-z0-9_]{3,50}$');

-- Password hash length validation (BCrypt hashes are 60 characters)
ALTER TABLE users ADD CONSTRAINT users_password_length
    CHECK (LENGTH(hashed_password) >= 60);
```

#### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Composite index for active user lookups
CREATE INDEX idx_users_active_email ON users(is_active, email) WHERE is_active = TRUE;
CREATE INDEX idx_users_active_username ON users(is_active, username) WHERE is_active = TRUE;
```

### User Sessions Table (Optional)

Optional table for JWT token management and session tracking. Useful for token blacklisting and audit trails.

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    token_type VARCHAR(20) DEFAULT 'access' CHECK (token_type IN ('access', 'refresh')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE NULL,
    user_agent TEXT,
    ip_address INET,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### Field Specifications

- **id**: UUID primary key
- **user_id**: Foreign key to users table with cascade delete
- **token_jti**: JWT ID claim, unique identifier for each token
- **token_type**: Type of token (access/refresh) for different handling
- **expires_at**: Token expiration timestamp
- **created_at**: Session creation timestamp
- **revoked_at**: Manual revocation timestamp (NULL if not revoked)
- **user_agent**: Client information for security monitoring
- **ip_address**: Client IP address for security analysis
- **is_active**: Session active status

#### Indexes

```sql
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token_jti ON user_sessions(token_jti);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_sessions_active ON user_sessions(is_active, expires_at);

-- Cleanup index for expired sessions
CREATE INDEX idx_sessions_cleanup ON user_sessions(expires_at, is_active)
    WHERE expires_at < CURRENT_TIMESTAMP;
```

### Audit Log Table (Future Enhancement)

Table for tracking user actions and security events.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Indexes

```sql
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_success ON audit_logs(success);

-- JSONB index for details queries
CREATE INDEX idx_audit_logs_details ON audit_logs USING GIN (details);
```

## Database Triggers

### Updated At Trigger

Automatically update the `updated_at` field when records are modified.

```sql
-- Generic updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Password Change Audit Trigger

Log password changes for security monitoring.

```sql
CREATE OR REPLACE FUNCTION audit_password_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.hashed_password IS DISTINCT FROM NEW.hashed_password THEN
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
        VALUES (
            NEW.id,
            'password_changed',
            'user',
            NEW.id,
            jsonb_build_object(
                'changed_at', CURRENT_TIMESTAMP,
                'ip_address', current_setting('app.current_ip', true),
                'user_agent', current_setting('app.current_user_agent', true)
            )
        );
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER audit_user_password_changes
    AFTER UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION audit_password_change();
```

## Data Migration Strategy

### Alembic Configuration

SQLAlchemy migrations using Alembic for version control and rollback capability.

```python
# alembic/env.py configuration
from app.core.config import settings
from app.models.base import Base

# Migration target metadata
target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode with actual database connection."""
    connectable = create_engine(settings.DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()
```

### Initial Migration

```sql
-- Version: 001_initial_schema.py
"""Initial user authentication schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 12:00:00.000000

"""

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_username', 'users', ['username'], unique=True)

    # Create updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    op.execute("""
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

def downgrade():
    op.drop_table('users')
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;")
```

## Performance Considerations

### Query Optimization

1. **User Lookup Queries**
   ```sql
   -- Optimized login query (uses index on email/username + is_active)
   SELECT id, email, username, hashed_password, is_active
   FROM users
   WHERE (email = $1 OR username = $1) AND is_active = TRUE;
   ```

2. **Session Cleanup**
   ```sql
   -- Efficient expired session cleanup
   DELETE FROM user_sessions
   WHERE expires_at < CURRENT_TIMESTAMP
   AND is_active = FALSE;
   ```

3. **Active User Count**
   ```sql
   -- Fast active user counting
   SELECT COUNT(*) FROM users WHERE is_active = TRUE;
   ```

### Connection Pooling

SQLAlchemy configuration for optimal connection management:

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Number of persistent connections
    max_overflow=20,  # Additional connections when pool full
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections every hour
    echo=False  # Set True for SQL debugging
)
```

## Security Measures

### Row Level Security (Future Enhancement)

For multi-tenant scenarios:

```sql
-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy for users to only see their own data
CREATE POLICY users_isolation_policy ON users
    FOR ALL
    TO application_user
    USING (id = current_setting('app.current_user_id')::UUID);
```

### Encryption at Rest

- Database-level encryption for sensitive columns
- Application-level encryption for PII data
- Backup encryption configuration

### Data Anonymization

For development/testing environments:

```sql
-- Anonymize user data for development
UPDATE users SET
    email = CONCAT('user', id, '@example.com'),
    username = CONCAT('user', substring(id::text, 1, 8))
WHERE environment = 'development';
```

## Backup and Recovery

### Backup Strategy

1. **Daily Full Backups**: Complete database dump
2. **Continuous WAL Archiving**: Point-in-time recovery
3. **Cross-region Replication**: Disaster recovery

### Recovery Procedures

```bash
# Point-in-time recovery example
pg_basebackup -h primary-server -D /backup/base -U replication -P -W

# Restore from backup
pg_restore --clean --create --verbose --host=localhost --username=postgres backup.dump
```

## Monitoring and Maintenance

### Database Health Checks

```sql
-- Connection count monitoring
SELECT COUNT(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';

-- Table size monitoring
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage statistics
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;
```

### Automated Maintenance

```sql
-- Automated VACUUM and ANALYZE
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule daily maintenance
SELECT cron.schedule('database-maintenance', '0 2 * * *', 'VACUUM ANALYZE;');

-- Cleanup expired sessions weekly
SELECT cron.schedule(
    'cleanup-sessions',
    '0 3 * * 0',
    'DELETE FROM user_sessions WHERE expires_at < NOW() - INTERVAL ''7 days'';'
);
```

This database schema provides a solid foundation for the authentication service with considerations for security, performance, and maintainability.