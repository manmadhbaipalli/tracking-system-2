# DevOps Documentation: Insurance Management System

## Overview

This document provides comprehensive deployment and operations guidance for the Integrated Policy, Claims, and Payments Platform. The system is containerized using Docker and can be deployed using various orchestration platforms.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [CI/CD Pipeline](#ci-cd-pipeline)
7. [Monitoring and Health Checks](#monitoring-and-health-checks)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

## System Architecture

### Components

- **Application Server**: FastAPI application running on Python 3.11
- **Database**: PostgreSQL 16 with connection pooling
- **Cache**: Redis 7 for session management and caching
- **Web Server**: Nginx as reverse proxy and load balancer
- **Container Orchestration**: Docker Compose for development, ECS/Kubernetes for production

### Network Architecture

```
[Internet] → [Load Balancer] → [Nginx] → [FastAPI Application] → [PostgreSQL]
                                                    ↓
                                               [Redis Cache]
```

### Service Dependencies

```mermaid
graph TD
    A[Nginx] --> B[FastAPI App]
    B --> C[PostgreSQL]
    B --> D[Redis]
    B --> E[External APIs]
    E --> F[Stripe]
    E --> G[Banking APIs]
    E --> H[Xactimate]
    E --> I[EDI Systems]
```

## Prerequisites

### Development Environment

- Docker Desktop 4.0+
- Docker Compose 2.0+
- Git
- Text editor (VS Code recommended)

### Production Environment

- Container orchestration platform (ECS, Kubernetes, or Docker Swarm)
- Load balancer (ALB, NGINX Plus, or similar)
- Managed database service (RDS PostgreSQL 16+)
- Managed cache service (ElastiCache Redis 7+)
- SSL certificate management
- Monitoring and logging infrastructure

## Environment Configuration

### Environment Variables

The application uses environment-based configuration. All sensitive values should be managed through your deployment platform's secret management system.

#### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE__POSTGRESQL_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | JWT signing key (min 32 chars) | `your-super-secret-jwt-key-32-chars-min!` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |

#### External Integration Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `INTEGRATIONS__STRIPE_SECRET_KEY` | Stripe API secret key | Yes |
| `INTEGRATIONS__STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | Yes |
| `INTEGRATIONS__STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | Yes |
| `INTEGRATIONS__ACH_API_KEY` | ACH processing API key | Yes |
| `INTEGRATIONS__WIRE_TRANSFER_API_KEY` | Wire transfer API key | Yes |
| `INTEGRATIONS__XACTIMATE_API_KEY` | Xactimate integration key | Optional |
| `INTEGRATIONS__EDI_API_KEY` | EDI systems API key | Optional |

#### Security Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENCRYPTION_KEY` | Data encryption key | Required for production |
| `MAX_FAILED_LOGIN_ATTEMPTS` | Account lockout threshold | 5 |
| `SESSION_TIMEOUT_MINUTES` | Session timeout | 480 (8 hours) |
| `REQUIRE_2FA` | Enable 2FA requirement | false |

### Configuration Files

1. **`.env.production`**: Production environment variables template
2. **`config/application-prod.yml`**: Application-specific production settings
3. **`docker-compose.yml`**: Production Docker Compose configuration
4. **`docker-compose.override.yml`**: Development overrides

## Docker Deployment

### Development Deployment

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd claim-system
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.production .env
   # Edit .env with your configuration
   ```

3. **Start development services:**
   ```bash
   # Start with development tools
   docker-compose --profile dev-tools up -d

   # Or start minimal stack
   docker-compose up -d
   ```

4. **Run database migrations:**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

5. **Access the application:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database Admin: http://localhost:8080 (Adminer)
   - Mail Testing: http://localhost:8025 (MailHog)

### Production Deployment with Docker Compose

1. **Prepare production environment:**
   ```bash
   # Copy and customize production configuration
   cp .env.production .env
   vi .env  # Configure all required variables

   # Create SSL certificate directory
   mkdir -p docker/nginx/ssl
   # Place your SSL certificates in docker/nginx/ssl/
   ```

2. **Deploy production stack:**
   ```bash
   # Pull latest images
   docker-compose pull

   # Start production services
   docker-compose -f docker-compose.yml up -d

   # Apply database migrations
   docker-compose exec app alembic upgrade head
   ```

3. **Verify deployment:**
   ```bash
   # Check service health
   docker-compose ps
   docker-compose exec app curl -f http://localhost:8000/health

   # Check logs
   docker-compose logs -f app
   ```

## Production Deployment

### AWS ECS Deployment

1. **Prepare infrastructure:**
   ```bash
   # Create ECS cluster
   aws ecs create-cluster --cluster-name insurance-production

   # Create task definition (see CI/CD pipeline)
   # Create ECS service with load balancer
   ```

2. **Database setup:**
   ```bash
   # Create RDS PostgreSQL instance
   aws rds create-db-instance \
     --db-instance-identifier insurance-prod-db \
     --db-instance-class db.r6g.large \
     --engine postgres \
     --engine-version 16.1 \
     --master-username postgres \
     --master-user-password <secure-password> \
     --allocated-storage 100 \
     --storage-type gp3 \
     --vpc-security-group-ids sg-xxx \
     --db-subnet-group-name insurance-subnet-group \
     --backup-retention-period 7 \
     --multi-az
   ```

3. **Redis setup:**
   ```bash
   # Create ElastiCache Redis cluster
   aws elasticache create-replication-group \
     --replication-group-id insurance-redis \
     --description "Insurance app Redis cluster" \
     --num-cache-clusters 2 \
     --cache-node-type cache.r6g.large \
     --engine redis \
     --engine-version 7.0 \
     --security-group-ids sg-xxx \
     --subnet-group-name insurance-cache-subnet-group
   ```

### Kubernetes Deployment

1. **Create namespace:**
   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: insurance-production
   ```

2. **Deploy using Helm:**
   ```bash
   # Add custom Helm chart
   helm install insurance-app ./helm/insurance-app \
     --namespace insurance-production \
     --set image.tag=latest \
     --set database.url=$DATABASE_URL \
     --set redis.url=$REDIS_URL
   ```

## CI/CD Pipeline

The GitHub Actions pipeline provides automated:

### Pipeline Stages

1. **Test Stage:**
   - Code quality checks (flake8, black, mypy)
   - Unit and integration tests
   - Security scanning (bandit, Trivy)
   - Coverage reporting

2. **Build Stage:**
   - Multi-architecture Docker image build
   - Image vulnerability scanning
   - SBOM generation
   - Registry push

3. **Deploy Stages:**
   - Staging deployment (develop branch)
   - Production deployment (releases)
   - Smoke testing
   - Rollback capabilities

### Setup Requirements

1. **GitHub Secrets:**
   ```
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   AWS_REGION
   SLACK_WEBHOOK_URL
   DOCKER_REGISTRY_USERNAME
   DOCKER_REGISTRY_PASSWORD
   ```

2. **Environment Protection Rules:**
   - Staging: Auto-deploy from develop branch
   - Production: Manual approval required

### Pipeline Configuration

The pipeline is configured in `.github/workflows/ci.yml` with:
- Parallel test execution
- Security scanning
- Multi-architecture builds
- Blue-green deployments
- Automated rollbacks

## Monitoring and Health Checks

### Health Check Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `/health` | Basic application health | `{"status": "healthy", "version": "1.0.0"}` |
| `/health/detailed` | Detailed health with dependencies | Component statuses |
| `/metrics` | Prometheus metrics | Application and business metrics |

### Key Metrics

1. **Application Metrics:**
   - Request rate and response time
   - Error rates by endpoint
   - Active sessions and concurrent users

2. **Business Metrics:**
   - Policy searches per minute
   - Claims processed per hour
   - Payment transactions per day
   - API response times by operation

3. **Infrastructure Metrics:**
   - Container CPU and memory usage
   - Database connection pool utilization
   - Redis cache hit ratio

### Monitoring Setup

1. **Prometheus Configuration:**
   ```yaml
   scrape_configs:
   - job_name: 'insurance-app'
     static_configs:
     - targets: ['app:8000']
     metrics_path: '/metrics'
   ```

2. **Grafana Dashboards:**
   - Application Performance Dashboard
   - Business Metrics Dashboard
   - Infrastructure Health Dashboard

3. **Alerting Rules:**
   ```yaml
   groups:
   - name: insurance-app
     rules:
     - alert: HighErrorRate
       expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
       for: 2m
     - alert: DatabaseConnectionsHigh
       expr: db_connections_active / db_connections_max > 0.8
       for: 5m
   ```

## Security Considerations

### Application Security

1. **Authentication & Authorization:**
   - JWT tokens with configurable expiration
   - Role-based access control
   - Account lockout after failed attempts

2. **Data Protection:**
   - PII encryption at rest
   - Data masking in logs and responses
   - Secure session management

3. **API Security:**
   - Rate limiting by IP and user
   - CORS configuration
   - Input validation and sanitization

### Infrastructure Security

1. **Network Security:**
   - Private subnets for databases
   - Security groups with minimal access
   - SSL/TLS termination at load balancer

2. **Container Security:**
   - Non-root user in containers
   - Minimal base images (Alpine Linux)
   - Regular security updates

3. **Secret Management:**
   - AWS Secrets Manager or similar
   - No secrets in container images
   - Regular secret rotation

### Compliance

- **PCI-DSS**: Payment data encryption and tokenization
- **SOX**: Audit trail and data retention
- **GDPR**: Data privacy and right to deletion

## Troubleshooting

### Common Issues

1. **Application Won't Start:**
   ```bash
   # Check environment variables
   docker-compose exec app env | grep -E "(DATABASE|JWT|REDIS)"

   # Check database connectivity
   docker-compose exec app python -c "
   from app.core.database import engine
   import asyncio
   asyncio.run(engine.connect())
   "

   # Check application logs
   docker-compose logs -f app
   ```

2. **Database Connection Issues:**
   ```bash
   # Test PostgreSQL connection
   docker-compose exec postgres psql -U postgres -d insurance -c "SELECT 1;"

   # Check connection pool status
   curl http://localhost:8000/health/detailed
   ```

3. **Performance Issues:**
   ```bash
   # Check resource usage
   docker stats

   # Monitor slow queries
   docker-compose exec postgres psql -U postgres -d insurance -c "
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   "
   ```

### Debugging

1. **Enable Debug Logging:**
   ```bash
   # Set environment variable
   export LOG_LEVEL=DEBUG

   # Restart application
   docker-compose restart app
   ```

2. **Database Query Logging:**
   ```bash
   # Enable SQLAlchemy echo
   export DATABASE__ECHO=true
   ```

3. **Performance Profiling:**
   ```python
   # Add to development environment
   import cProfile
   cProfile.run('your_function()')
   ```

## Maintenance

### Regular Maintenance Tasks

1. **Database Maintenance:**
   ```bash
   # Weekly database statistics update
   docker-compose exec postgres psql -U postgres -d insurance -c "ANALYZE;"

   # Monthly vacuum
   docker-compose exec postgres psql -U postgres -d insurance -c "VACUUM;"
   ```

2. **Log Rotation:**
   ```bash
   # Configure log rotation
   docker-compose exec app logrotate /etc/logrotate.d/insurance-app
   ```

3. **Security Updates:**
   ```bash
   # Update base images monthly
   docker-compose pull
   docker-compose up -d

   # Update Python dependencies
   pip-audit
   ```

### Backup and Recovery

1. **Database Backups:**
   ```bash
   # Daily automated backup
   docker-compose exec postgres pg_dump -U postgres insurance > backup_$(date +%Y%m%d).sql

   # Restore from backup
   docker-compose exec -T postgres psql -U postgres insurance < backup_20240101.sql
   ```

2. **Application Data Backups:**
   ```bash
   # Backup uploaded files
   docker-compose exec app tar -czf /app/data/uploads_backup_$(date +%Y%m%d).tar.gz /app/uploads/

   # Backup configuration
   cp .env .env.backup.$(date +%Y%m%d)
   ```

### Scaling Considerations

1. **Horizontal Scaling:**
   - Stateless application design allows multiple instances
   - Database connection pooling handles increased load
   - Redis session storage enables load balancing

2. **Vertical Scaling:**
   - Monitor CPU and memory usage
   - Adjust container resource limits
   - Scale database and Redis instances

3. **Performance Optimization:**
   - Database query optimization
   - Caching strategy refinement
   - CDN for static assets

---

## Quick Reference

### Essential Commands

```bash
# Start development environment
docker-compose --profile dev-tools up -d

# View application logs
docker-compose logs -f app

# Execute database migration
docker-compose exec app alembic upgrade head

# Access application shell
docker-compose exec app python -m app.shell

# Run tests
docker-compose exec app pytest

# Check health
curl http://localhost:8000/health

# Scale application
docker-compose up -d --scale app=3

# Backup database
docker-compose exec postgres pg_dump -U postgres insurance > backup.sql

# Monitor resource usage
docker stats
```

### Emergency Procedures

1. **Service Outage:**
   - Check health endpoint
   - Review application logs
   - Verify database connectivity
   - Check external service status

2. **Data Recovery:**
   - Stop application
   - Restore from latest backup
   - Apply recent migrations
   - Verify data integrity

3. **Security Incident:**
   - Rotate all secrets immediately
   - Review audit logs
   - Check for unauthorized access
   - Update security configurations

For additional support, consult the project documentation or contact the development team.