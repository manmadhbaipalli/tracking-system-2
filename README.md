# Auth Service - FastAPI Authentication Service

A comprehensive FastAPI-based authentication service with advanced features including centralized logging, exception handling, circuit breaker pattern, and automatic API documentation.

## Features

- 🔐 **Authentication & Authorization**
  - User registration and login endpoints
  - JWT token-based authentication
  - Password hashing with bcrypt
  - User management and profile handling

- 🔧 **Infrastructure Features**
  - Centralized logging system with structured logging
  - Global exception handling with custom error responses
  - Circuit breaker pattern for fault tolerance
  - Database connection pooling and management

- 📚 **API Documentation**
  - Automatic Swagger/OpenAPI documentation
  - Interactive API explorer
  - Comprehensive endpoint documentation

- 🧪 **Testing & Quality**
  - Comprehensive test suite with pytest
  - Code coverage reporting
  - Type checking with MyPy
  - Code formatting with Black

## Tech Stack

- **Backend**: FastAPI 0.104+, Python 3.11+
- **Database**: SQLAlchemy with PostgreSQL/SQLite support
- **Authentication**: JWT tokens with python-jose
- **Logging**: Structlog for structured logging
- **Testing**: Pytest with async support
- **Documentation**: Swagger/OpenAPI auto-generation
- **Code Quality**: Black, isort, flake8, MyPy

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional but recommended)
- PostgreSQL (optional, SQLite used by default)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd auth-service
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

### Using Docker

1. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec auth-service alembic upgrade head
   ```

The application will be available at `http://localhost:8000`

## API Documentation

Once the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## API Endpoints

### Authentication Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout (requires authentication)
- `POST /api/auth/refresh` - Refresh JWT token

### User Management

- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update current user profile
- `DELETE /api/users/me` - Delete current user account

### Health Checks

- `GET /health` - Application health status
- `GET /health/db` - Database connection status

## Development

### Project Structure

```
auth-service/
├── app/                    # Application source code
│   ├── api/               # API routes and endpoints
│   ├── core/              # Core configuration and utilities
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── utils/             # Helper utilities
├── tests/                 # Test suite
├── docs/                  # Documentation and diagrams
├── alembic/               # Database migrations
└── monitoring/            # Monitoring configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

### Code Quality

```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Configuration

### Environment Variables

Key configuration options (see `.env.example` for full list):

```env
# Database
DATABASE_URL=sqlite:///./auth_service.db

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
LOG_LEVEL=INFO

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT_DURATION=60
```

### Database Configuration

The application supports both SQLite (development) and PostgreSQL (production):

```env
# SQLite (default)
DATABASE_URL=sqlite:///./auth_service.db

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/auth_service
```

## Monitoring and Logging

### Structured Logging

The application uses structured logging with contextual information:

```python
import structlog

logger = structlog.get_logger()
logger.info("User login attempt", user_id=user.id, ip_address="192.168.1.1")
```

### Circuit Breaker

Database operations are protected by circuit breaker pattern:

```python
from app.services.circuit_breaker import circuit_breaker

@circuit_breaker
async def get_user_by_email(email: str):
    # Database operation protected by circuit breaker
    pass
```

### Health Checks

Monitor application health:

```bash
# Basic health check
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db
```

## Deployment

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Environment-specific configurations**
   ```bash
   # Development
   docker-compose up -d

   # With monitoring
   docker-compose --profile monitoring up -d
   ```

### Production Considerations

- Use PostgreSQL instead of SQLite
- Set strong `SECRET_KEY`
- Configure proper CORS settings
- Set up reverse proxy (Nginx)
- Enable HTTPS/TLS
- Configure log aggregation
- Set up monitoring and alerting

## Security Features

- **Password Security**: Bcrypt hashing with salt
- **JWT Tokens**: Secure token generation and validation
- **Input Validation**: Pydantic schemas with comprehensive validation
- **CORS Protection**: Configurable cross-origin resource sharing
- **Rate Limiting**: Protection against brute force attacks
- **Audit Logging**: Comprehensive security event logging

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run code quality checks (`black`, `flake8`, `mypy`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the sequence diagrams in the `/docs` directory