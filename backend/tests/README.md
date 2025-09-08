# Testing Documentation

This directory contains comprehensive tests for the Flowstate backend, specifically focusing on the Notion OAuth integration.

## Test Structure

```
tests/
├── run_tests.py              # Main test runner
├── oauth/
│   └── test_notion_oauth.py  # OAuth-specific tests
└── integration/
    └── test_backend_integration.py  # Backend integration tests
```

## Running Tests

### Run All Tests
```bash
cd backend
python tests/run_tests.py
```

### Run Specific Test Suites
```bash
# OAuth tests only
python tests/run_tests.py --oauth-only

# Integration tests only  
python tests/run_tests.py --integration-only
```

### Individual Test Files
```bash
# OAuth tests
python tests/oauth/test_notion_oauth.py

# Integration tests
python tests/integration/test_backend_integration.py
```

## Test Coverage

### OAuth Tests (`oauth/test_notion_oauth.py`)
- ✅ Environment configuration validation
- ✅ OAuth URL generation and validation
- ✅ Token service integration
- ✅ Security features (CSRF protection, unique states)

### Integration Tests (`integration/test_backend_integration.py`)
- ✅ Backend health checks
- ✅ API endpoint availability
- ✅ Database connectivity
- ✅ Environment variable validation
- ✅ CORS configuration

## Prerequisites

Before running tests, ensure:

1. **Backend is running**:
   ```bash
   cd backend
   python app.py
   ```

2. **Environment variables are set**:
   - `NOTION_OAUTH_CLIENT_ID`
   - `NOTION_OAUTH_CLIENT_SECRET`
   - `NOTION_OAUTH_REDIRECT_URI`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`

3. **Dependencies are installed**:
   ```bash
   pip install -r requirements.txt
   ```

## Test Results

Tests will output detailed results including:
- ✅ Passed tests
- ❌ Failed tests with error details
- ⚠️ Warnings for non-critical issues
- 📊 Summary statistics

## Troubleshooting

### Common Issues

1. **Backend not running**:
   ```
   ❌ Cannot connect to backend at http://localhost:8000
   ```
   **Solution**: Start the backend with `python app.py`

2. **Missing environment variables**:
   ```
   ❌ Missing environment variables: ['NOTION_OAUTH_CLIENT_ID']
   ```
   **Solution**: Check your `.env` file and ensure all required variables are set

3. **OAuth configuration issues**:
   ```
   ❌ REDIRECT_URI contains the full OAuth URL
   ```
   **Solution**: Update `NOTION_OAUTH_REDIRECT_URI` to be just the callback endpoint

### Debug Mode

For more detailed output, you can run individual test files directly:
```bash
python tests/oauth/test_notion_oauth.py
```

This will provide more verbose output for debugging specific issues.

## Adding New Tests

To add new tests:

1. **For OAuth functionality**: Add to `oauth/test_notion_oauth.py`
2. **For backend integration**: Add to `integration/test_backend_integration.py`
3. **For new service areas**: Create new test files in appropriate subdirectories

Follow the existing patterns:
- Use descriptive test names
- Include proper error handling
- Provide clear success/failure messages
- Add documentation for test purposes
