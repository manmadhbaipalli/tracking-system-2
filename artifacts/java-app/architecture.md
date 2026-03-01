# Architecture Design Document

## Overview
Simple Java Spring Boot REST API application with user authentication and basic CRUD operations.

## Technology Stack
- **Framework**: Spring Boot 3.4.1
- **Language**: Java 21
- **Database**: H2 (dev), PostgreSQL (prod)
- **Security**: Spring Security + JWT
- **API Docs**: SpringDoc OpenAPI
- **Build Tool**: Maven

## System Architecture

### Layers
1. **Controller Layer**: REST endpoints, request/response handling
2. **Service Layer**: Business logic, transaction management
3. **Repository Layer**: Database access via Spring Data JPA
4. **Security Layer**: Authentication, authorization, JWT handling

### Core Components

#### Entities
- **User**: Core user entity with authentication details
  - Fields: id, email, passwordHash, name, role (ADMIN/USER), active status, timestamps

#### API Endpoints
- **Auth Endpoints** (`/api/v1/auth`)
  - POST /register - User registration
  - POST /login - User login (returns JWT)

- **User Endpoints** (`/api/v1/users`)
  - GET /{id} - Get user by ID (authenticated)
  - PUT /{id} - Update user (authenticated, own record only)
  - DELETE /{id} - Deactivate user (authenticated, own record only)

#### Security
- JWT-based authentication
- Role-based access control (RBAC)
- Correlation ID tracking for request tracing
- BCrypt password hashing
- CORS configuration

#### Observability
- Structured JSON logging (production)
- Health check endpoints via Actuator
- Correlation ID in all log entries
- Request/response logging at boundaries

## Database Schema

### User Table
```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

## Security Design

### Authentication Flow
1. User registers via /api/v1/auth/register
2. User logs in via /api/v1/auth/login with email/password
3. Server validates credentials and returns JWT token
4. Client includes JWT in Authorization header for subsequent requests
5. JwtAuthFilter validates token and sets SecurityContext

### Authorization
- Public endpoints: /api/v1/auth/**, /actuator/health, /swagger-ui/**
- All other endpoints require authentication
- Users can only access/modify their own data

## Error Handling
- Global exception handler for consistent error responses
- Custom exceptions: NotFoundException, ConflictException, AuthException
- Validation error handling with field-level details
- No stack traces exposed to clients

## Configuration Management
- Environment-specific profiles (dev, prod)
- Externalized configuration via environment variables
- Secrets never in source code or config files
