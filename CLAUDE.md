# Simple Java Spring Boot Application

## Project Standards

### Package Structure
- `src/main/java/com/example/simpleapp/` - main application package
- `src/main/java/com/example/simpleapp/model/` - JPA entities
- `src/main/java/com/example/simpleapp/repository/` - Spring Data JPA repositories
- `src/main/java/com/example/simpleapp/controller/` - REST controllers
- `src/main/java/com/example/simpleapp/dto/` - Data Transfer Objects
- `src/main/java/com/example/simpleapp/service/` - Business logic layer
- `src/main/java/com/example/simpleapp/config/` - Configuration classes
- `src/main/java/com/example/simpleapp/security/` - Security components (JWT, filters)
- `src/main/java/com/example/simpleapp/filter/` - Request filters
- `src/main/java/com/example/simpleapp/exception/` - Custom exceptions and handlers
- `artifacts/java-app/` - Project documentation and specs

### Code Style
- Use constructor injection (never field injection with @Autowired)
- PascalCase for classes
- camelCase for methods and variables
- Use records for immutable DTOs
- Add Javadoc for public APIs
- Use SLF4J for logging

### Maven Coordinates
- **groupId**: com.example
- **artifactId**: simple-app
- **version**: 0.0.1-SNAPSHOT

### Commands
- Build: `mvn clean package`
- Run: `mvn spring-boot:run`
- Compile: `mvn compile`
- Test: `mvn test`
- Access app: `http://localhost:8080`
- Access Swagger UI: `http://localhost:8080/swagger-ui.html`
- Health check: `http://localhost:8080/actuator/health`

### Key Dependencies
- Spring Boot 3.4.1 (Web, Data JPA, Security, Validation, Actuator)
- JWT (jjwt 0.12.6)
- H2 Database (dev profile)
- PostgreSQL (prod profile)
- SpringDoc OpenAPI 2.8.4
- Logstash Logback Encoder 8.0
