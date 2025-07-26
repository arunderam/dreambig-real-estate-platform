# API Testing Scripts - DreamBig Real Estate Platform

This directory contains utility scripts for testing and working with the DreamBig Real Estate Platform API.

## 📋 Available Scripts

### 1. 🔑 Authentication Token Generator (`generate_auth_token.py`)

Comprehensive script for generating JWT authentication tokens for API testing.

**Features:**
- Generate tokens for existing users
- Create new test users with tokens
- Support for different user roles (tenant, owner, admin)
- Multiple output formats (JSON, curl, header, token-only)
- Token expiration customization
- User listing functionality

**Usage:**
```bash
# Generate token for existing user by email
python scripts/generate_auth_token.py --email user@example.com

# Generate token for existing user by ID
python scripts/generate_auth_token.py --user-id 1

# Create new user and generate token
python scripts/generate_auth_token.py --create-user --email test@example.com --name "Test User"

# Create admin user
python scripts/generate_auth_token.py --create-user --email admin@example.com --name "Admin User" --role admin

# Generate token with custom expiration (120 minutes)
python scripts/generate_auth_token.py --email user@example.com --expires 120

# Output in different formats
python scripts/generate_auth_token.py --email user@example.com --format curl
python scripts/generate_auth_token.py --email user@example.com --format header
python scripts/generate_auth_token.py --email user@example.com --format token

# List existing users
python scripts/generate_auth_token.py --list-users

# Save token to file
python scripts/generate_auth_token.py --email user@example.com --save token.txt
```

### 2. ⚡ Quick Token Generator (`quick_token.py`)

Simple script for quickly generating tokens for common test scenarios.

**Features:**
- Predefined test users (tenant, owner, admin)
- Quick token generation
- Automatic user creation if needed
- Copy-paste ready output

**Usage:**
```bash
# Default tenant user
python scripts/quick_token.py

# Admin user
python scripts/quick_token.py admin

# Property owner
python scripts/quick_token.py owner

# Custom user
python scripts/quick_token.py custom email@test.com "Test User"
```

**Output:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "tenant@dreambig.com",
    "name": "Test Tenant",
    "role": "tenant"
  }
}
```

### 3. 📮 Postman Collection Generator (`generate_postman_collection.py`)

Generates a complete Postman collection with pre-configured requests and authentication tokens.

**Features:**
- Complete API endpoint coverage
- Pre-configured authentication tokens
- Organized request folders
- Environment variables
- Sample request bodies

**Usage:**
```bash
# Generate collection with default settings
python scripts/generate_postman_collection.py

# Custom output file
python scripts/generate_postman_collection.py --output my_api.json

# Custom base URL
python scripts/generate_postman_collection.py --base-url https://api.dreambig.com

# Generate without tokens
python scripts/generate_postman_collection.py --no-tokens
```

**Generated Collection Includes:**
- **Authentication**: Register, login, profile management, password reset
- **Properties**: CRUD operations, search, recommendations, comparison
- **Admin**: User management, system operations
- **Pre-configured Variables**: Base URL, authentication tokens
- **Sample Data**: Realistic request bodies and parameters

### 4. 🧪 API Endpoint Tester (`test_api_endpoints.py`)

Comprehensive script for testing all major API endpoints with automated token generation.

**Features:**
- Automated authentication token generation
- Complete endpoint coverage
- Performance testing
- Success/failure reporting
- Response time measurement
- Detailed logging

**Usage:**
```bash
# Test all endpoints
python scripts/test_api_endpoints.py

# Test with custom base URL
python scripts/test_api_endpoints.py --base-url https://api.dreambig.com

# Verbose output
python scripts/test_api_endpoints.py --verbose

# Save results to file
python scripts/test_api_endpoints.py --save-results
```

**Test Categories:**
- **Authentication Tests**: Token validation, role-based access
- **Property Tests**: CRUD operations, search functionality
- **Performance Tests**: Response time benchmarks
- **Authorization Tests**: Permission validation

## 🚀 Quick Start Guide

### 1. Generate a Quick Token
```bash
# Get a tenant token for testing
python scripts/quick_token.py

# Copy the token from output and use in API calls
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/auth/me
```

### 2. Test API Endpoints
```bash
# Run comprehensive API tests
python scripts/test_api_endpoints.py --verbose
```

### 3. Generate Postman Collection
```bash
# Create Postman collection for manual testing
python scripts/generate_postman_collection.py
# Import the generated .json file into Postman
```

### 4. Create Custom Test Users
```bash
# Create an admin user for testing
python scripts/generate_auth_token.py --create-user --email admin@test.com --name "Test Admin" --role admin

# Create a property owner
python scripts/generate_auth_token.py --create-user --email owner@test.com --name "Test Owner" --role owner
```

## 📊 Common Use Cases

### Manual API Testing
1. Generate a token: `python scripts/quick_token.py`
2. Use token in curl/Postman: `Authorization: Bearer TOKEN`
3. Test endpoints manually

### Automated Testing
1. Run endpoint tests: `python scripts/test_api_endpoints.py`
2. Review test results and performance metrics
3. Fix any failing endpoints

### Development Setup
1. Create test users: `python scripts/generate_auth_token.py --create-user ...`
2. Generate Postman collection: `python scripts/generate_postman_collection.py`
3. Import collection into Postman for development

### CI/CD Integration
1. Use scripts in automated pipelines
2. Generate tokens for integration tests
3. Validate API endpoints automatically

## 🔧 Configuration

### Environment Variables
```bash
# Database configuration
export DATABASE_URL=sqlite:///./test.db

# JWT configuration
export SECRET_KEY=your_secret_key
export ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=30

# API configuration
export API_BASE_URL=http://localhost:8000
```

### Default Test Users
The scripts create these predefined test users:

| Role | Email | Name | Phone |
|------|-------|------|-------|
| tenant | tenant@dreambig.com | Test Tenant | +1234567890 |
| owner | owner@dreambig.com | Test Property Owner | +1234567891 |
| admin | admin@dreambig.com | Test Admin | +1234567892 |

## 🛠️ Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Ensure database is accessible
export DATABASE_URL=sqlite:///./test.db
# Or check PostgreSQL connection
```

**Import Errors**
```bash
# Run from project root directory
cd /path/to/dreambig
python scripts/quick_token.py
```

**Token Validation Errors**
```bash
# Check if API server is running
curl http://localhost:8000/api/v1/properties/

# Verify token format
python scripts/generate_auth_token.py --email user@example.com --format token
```

**User Not Found**
```bash
# List existing users
python scripts/generate_auth_token.py --list-users

# Create new user
python scripts/generate_auth_token.py --create-user --email new@example.com --name "New User"
```

### Debug Mode
Add `--verbose` flag to any script for detailed logging:
```bash
python scripts/test_api_endpoints.py --verbose
python scripts/generate_auth_token.py --email user@example.com --verbose
```

## 📚 Integration Examples

### With curl
```bash
# Get token
TOKEN=$(python scripts/quick_token.py | jq -r '.access_token')

# Use token in API calls
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/properties/
```

### With Python requests
```python
import requests
from scripts.quick_token import generate_quick_token

# Generate token
result = generate_quick_token("tenant")
token = result["access_token"]

# Make API call
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/v1/auth/me", headers=headers)
print(response.json())
```

### With Postman
1. Generate collection: `python scripts/generate_postman_collection.py`
2. Import the generated `.json` file into Postman
3. Tokens are pre-configured in collection variables
4. Start testing immediately

## 🔗 Related Documentation

- [API Documentation](../API_DOCUMENTATION.md)
- [Testing Guide](../TESTING.md)
- [Development Setup](../README.md)
- [Authentication Guide](../docs/authentication.md)
