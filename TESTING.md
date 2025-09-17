# Testing Guide for FlowState

This document outlines the testing strategy and setup for the FlowState project.

## Overview

FlowState uses a comprehensive testing approach with:
- **Backend**: Python pytest with FastAPI TestClient
- **Frontend**: Jest and React Testing Library
- **Integration**: End-to-end API testing
- **CI/CD**: GitHub Actions for automated testing

## Backend Testing

### Setup

```bash
cd backend
pip install -r requirements-test.txt
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=term --cov-report=html

# Run specific test categories
python -m pytest tests/ -m unit
python -m pytest tests/ -m integration
python -m pytest tests/ -m "not slow"
```

### Test Structure

```
backend/tests/
├── conftest.py          # Test configuration and fixtures
├── test_app.py          # FastAPI application tests
├── test_agents.py       # LangGraph agent tests
├── test_db_auth.py      # Database and authentication tests
├── test_integrations.py # External API integration tests
└── test_basic.py        # Basic functionality tests
```

### Test Categories

- **Unit Tests** (`@pytest.mark.unit`): Test individual functions and classes
- **Integration Tests** (`@pytest.mark.integration`): Test component interactions
- **Slow Tests** (`@pytest.mark.slow`): Tests that take longer to run
- **Auth Tests** (`@pytest.mark.auth`): Tests requiring authentication

### Environment Variables

Tests use these environment variables:
```bash
ENV=test
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=test-secret-key-for-testing-only
ANTHROPIC_API_KEY=test-key
OPENAI_API_KEY=test-key
```

## Frontend Testing

### Setup

```bash
cd frontend/flowstate
npm install
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- Button.test.tsx
```

### Test Structure

```
frontend/flowstate/src/tests/
├── setup.ts                    # Test environment setup
├── basic.test.ts              # Basic Jest functionality
├── Button.test.tsx            # Button component tests
├── Typography.test.tsx        # Typography component tests
├── config.test.tsx            # Configuration tests
├── integration.test.tsx       # Integration tests
└── langgraph-connection.test.tsx # LangGraph API tests
```

### Test Utilities

- **Jest**: JavaScript testing framework
- **React Testing Library**: React component testing
- **jsdom**: DOM environment for testing
- **ts-jest**: TypeScript support for Jest

## Integration Testing

### API Testing

The project includes API integration tests that verify:
- Backend API endpoints
- Frontend-backend communication
- LangGraph agent connectivity
- Database operations

### Running Integration Tests

```bash
# Start backend server
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 &

# Run frontend integration tests
cd frontend/flowstate
npm test -- integration.test.tsx
```

## CI/CD Testing

### GitHub Actions Workflows

1. **CI Pipeline** (`.github/workflows/ci.yml`):
   - Backend tests with pytest
   - Frontend tests with Jest
   - Code quality checks (linting, formatting)
   - Security scans
   - Docker build tests

2. **Branch Protection** (`.github/workflows/branch-protection.yml`):
   - PR validation
   - Size and complexity checks
   - Dependency security checks
   - Test coverage requirements

### Status Checks

The following checks must pass for PRs to main:
- ✅ Backend tests pass
- ✅ Frontend tests pass
- ✅ Code quality standards met
- ✅ No security vulnerabilities
- ✅ Test coverage ≥ 50%
- ✅ PR has adequate description
- ✅ No obvious secrets in code

## Test Coverage Goals

- **Backend**: Minimum 50% overall coverage
- **Frontend**: Minimum 40% overall coverage
- **Critical paths**: Minimum 80% coverage for auth, API, and core features

## Writing New Tests

### Backend Test Example

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.unit
def test_health_endpoint(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
```

### Frontend Test Example

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import Button from '@/components/Button'

describe('Button Component', () => {
  test('handles click events', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

## Debugging Tests

### Backend Debugging

```bash
# Run tests with verbose output
python -m pytest tests/ -v -s

# Run specific test with debugging
python -m pytest tests/test_app.py::test_health_endpoint -v -s

# Debug with pdb
python -m pytest tests/ --pdb
```

### Frontend Debugging

```bash
# Run tests with verbose output
npm test -- --verbose

# Debug specific test
npm test -- --testNamePattern="Button Component"

# Debug with Node.js debugger
node --inspect-brk node_modules/.bin/jest --runInBand
```

## Mock and Fixture Guidelines

### Backend Mocks

- Use `pytest.fixture` for reusable test data
- Mock external APIs and services
- Use `unittest.mock` for Python mocking
- Isolate database operations with test transactions

### Frontend Mocks

- Mock Next.js router and navigation
- Mock external API calls with Jest mocks
- Use MSW (Mock Service Worker) for complex API mocking
- Mock environment variables for testing

## Performance Testing

For performance-critical features:
- Add `@pytest.mark.slow` for longer-running tests
- Use `pytest-benchmark` for performance regression testing
- Monitor test execution time in CI
- Set reasonable timeouts for async operations

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Naming**: Test names should describe what is being tested
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Don't rely on external services
5. **Test Edge Cases**: Include error conditions and boundary cases
6. **Keep Tests Fast**: Unit tests should run quickly
7. **Meaningful Assertions**: Assert specific expected behaviors
8. **Documentation**: Comment complex test logic

## Troubleshooting

### Common Issues

1. **Import Errors**: Check Python/Node.js path configuration
2. **Database Errors**: Ensure test database is properly configured
3. **Async Test Issues**: Use proper async/await patterns
4. **Mock Failures**: Verify mock setup and teardown
5. **Environment Variables**: Check test environment configuration

### Getting Help

- Check test logs for specific error messages
- Review CI/CD pipeline output
- Consult this documentation
- Ask team members for assistance