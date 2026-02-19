# Database Schema Design

## Overview

This document outlines the database schema for the FastAPI authentication service. The schema is designed to support user authentication, session management, and audit logging.

## Database Tables

### Users Table

The main table for storing user account information.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_users_created_at ON users(created_at);
```

**Fields Description:**
- `id`: Primary key using UUID for better security and scalability
- `email`: User's email address, must be unique and used for login
- `username`: User's chosen username, must be unique and used for login
- `hashed_password`: Bcrypt hashed password, never store plain text
- `first_name`, `last_name`: Optional user profile information
- `is_active`: Soft delete flag, inactive users cannot login
- `is_superuser`: Administrative privileges flag
- `is_verified`: Email verification status
- `created_at`: Account creation timestamp
- `updated_at`: Last profile update timestamp
- `last_login`: Last successful login timestamp

### User Sessions Table (Optional)

For managing JWT token blacklisting and session tracking.

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    token_type VARCHAR(20) NOT NULL DEFAULT 'access',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    user_agent TEXT,
    ip_address INET
);

-- Indexes for performance
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token_jti ON user_sessions(token_jti);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_sessions_active ON user_sessions(is_revoked) WHERE is_revoked = FALSE;

-- Cleanup expired sessions
CREATE INDEX idx_sessions_cleanup ON user_sessions(expires_at, is_revoked);
```

**Fields Description:**
- `id`: Primary key for the session record
- `user_id`: Foreign key reference to users table
- `token_jti`: JWT ID claim for token identification
- `token_type`: Type of token (access, refresh)
- `expires_at`: When the token expires
- `is_revoked`: Flag to revoke tokens before expiration
- `revoked_at`: Timestamp when token was revoked
- `user_agent`: Browser/client information for security tracking
- `ip_address`: IP address where token was issued

### Audit Log Table

For tracking authentication events and security monitoring.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance and querying
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_success ON audit_logs(success);
CREATE INDEX idx_audit_event_data ON audit_logs USING GIN(event_data);
```

**Fields Description:**
- `id`: Primary key for the audit record
- `user_id`: User associated with the event (nullable for failed login attempts)
- `event_type`: Type of event (LOGIN, LOGOUT, REGISTER, PASSWORD_CHANGE, etc.)
- `event_data`: Additional event-specific data in JSON format
- `ip_address`: Client IP address
- `user_agent`: Client browser/application information
- `success`: Whether the operation succeeded
- `error_message`: Error details if operation failed
- `created_at`: Event timestamp

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│     USERS       │       │ USER_SESSIONS   │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │ 1   * │ id (PK)         │
│ email (UNIQUE)  │ ──────│ user_id (FK)    │
│ username (UNIQUE)│       │ token_jti       │
│ hashed_password │       │ token_type      │
│ first_name      │       │ expires_at      │
│ last_name       │       │ is_revoked      │
│ is_active       │       │ created_at      │
│ is_superuser    │       │ revoked_at      │
│ is_verified     │       │ user_agent      │
│ created_at      │       │ ip_address      │
│ updated_at      │       └─────────────────┘
│ last_login      │
└─────────────────┘
        │
        │ 1
        │
        │ *
┌─────────────────┐
│   AUDIT_LOGS    │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ event_type      │
│ event_data      │
│ ip_address      │
│ user_agent      │
│ success         │
│ error_message   │
│ created_at      │
└─────────────────┘
```

## Database Migrations

### Migration Strategy

1. **Alembic Setup**: Use Alembic for database migrations
2. **Version Control**: Each schema change gets a versioned migration file
3. **Rollback Support**: All migrations should be reversible
4. **Data Migrations**: Separate data migrations from schema changes

### Initial Migration (001_initial_schema.py)

```python
"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )

    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_active', 'users', ['is_active'], postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_users_created_at', 'users', ['created_at'])

def downgrade():
    op.drop_table('users')
```

## Performance Considerations

### Indexing Strategy

1. **Primary Keys**: Automatic B-tree indexes on UUID primary keys
2. **Unique Constraints**: Automatic indexes on email and username
3. **Query Optimization**: Indexes on frequently queried columns
4. **Partial Indexes**: Only index active users for better performance
5. **Composite Indexes**: For complex queries (user_id + created_at)

### Query Optimization

1. **Connection Pooling**: Use SQLAlchemy connection pooling
2. **Query Limits**: Always use LIMIT in list queries
3. **Select Specific Columns**: Avoid SELECT * queries
4. **Prepared Statements**: Use parameterized queries to prevent SQL injection

### Maintenance

1. **VACUUM**: Regular table maintenance for PostgreSQL
2. **ANALYZE**: Update table statistics for query planner
3. **Archive Old Data**: Move old audit logs to archive tables
4. **Monitor Query Performance**: Use EXPLAIN ANALYZE for slow queries

## Security Considerations

### Data Protection

1. **Password Hashing**: Use bcrypt with sufficient rounds (12+)
2. **Personal Data**: Hash or encrypt sensitive personal information
3. **Audit Trails**: Log all authentication events
4. **Data Retention**: Define retention policies for sensitive data

### Access Control

1. **Row Level Security**: Implement RLS policies in PostgreSQL
2. **Database Users**: Use separate database users for different access levels
3. **Connection Encryption**: Always use SSL/TLS for database connections
4. **Backup Encryption**: Encrypt database backups

### Compliance

1. **GDPR**: Support for data deletion and export
2. **Data Minimization**: Only store necessary user data
3. **Consent Management**: Track user consent for data processing
4. **Right to be Forgotten**: Implement user data deletion procedures