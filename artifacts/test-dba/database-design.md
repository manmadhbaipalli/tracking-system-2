# Database Design: Auth Service

## ER Diagram (Text)

```
┌──────────┐     1:N     ┌──────────┐
│  users   │────────────>│  orders  │
└──────────┘             └──────────┘
                              │ 1:N
                              ▼
                         ┌────────────┐
                         │order_items │
                         └────────────┘
```

## Table Definitions

### users
| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | INTEGER | PK, AUTOINCREMENT | — |
| email | VARCHAR(255) | UNIQUE, NOT NULL | — |
| password_hash | VARCHAR(255) | NOT NULL | — |
| name | VARCHAR(100) | NOT NULL | — |
| role | VARCHAR(20) | NOT NULL | 'USER' |
| active | BOOLEAN | NOT NULL | TRUE |
| created_at | TIMESTAMP | NOT NULL | func.now() |
| updated_at | TIMESTAMP | NOT NULL | func.now() |

## Indexes

| Index Name | Table | Columns | Rationale |
|------------|-------|---------|-----------|
| idx_users_email | users | email | Login lookup |
| idx_users_active | users | active | Filter queries |