# FlowState Development Setup and Testing

## Quick Start for Contributors

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git
- Docker (optional, for full environment)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/lukebrevoort/flowstate.git
   cd flowstate
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend/flowstate
   npm install --legacy-peer-deps
   ```

4. **Environment Variables**
   Create `.env` files:
   
   `backend/.env`:
   ```
   ENV=development
   DATABASE_URL=sqlite:///./dev.db
   SECRET_KEY=your-secret-key-here
   ANTHROPIC_API_KEY=your-anthropic-key
   OPENAI_API_KEY=your-openai-key
   ```
   
   `frontend/flowstate/.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_LANGGRAPH_API_URL=http://localhost:9876
   ```

### Running Tests

#### Backend Tests
```bash
cd backend
python -m pytest tests/ -v --cov=. --cov-report=term
```

#### Frontend Tests
```bash
cd frontend/flowstate
npm test -- --watchAll=false
```

#### All Tests (from root)
```bash
# Run backend tests
cd backend && python -m pytest tests/ -v

# Run frontend tests  
cd frontend/flowstate && npm test -- --watchAll=false

# Run linting
cd frontend/flowstate && npm run lint
```

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following project conventions
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run all tests
   cd backend && python -m pytest tests/
   cd frontend/flowstate && npm test -- --watchAll=false
   
   # Check code quality
   cd frontend/flowstate && npm run lint
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Provide a clear description of changes
   - Ensure all CI checks pass
   - Request review from team members

### Branch Protection Rules

The `main` branch is protected with the following requirements:
- ✅ All status checks must pass
- ✅ Pull request reviews required
- ✅ Up-to-date with base branch
- ✅ No force pushes allowed
- ✅ Administrator privileges enforced

### CI/CD Pipeline

When you create a pull request, the following automated checks run:

1. **Backend Tests**
   - Unit and integration tests
   - Code coverage analysis
   - Dependency security checks

2. **Frontend Tests**
   - Component and utility tests
   - Build verification
   - Linting and code quality

3. **Code Quality**
   - Python formatting (Black, isort)
   - JavaScript/TypeScript linting (ESLint)
   - Security vulnerability scanning

4. **Docker Testing**
   - Container build verification
   - Basic health checks

### Manual Testing

For manual testing of the full application:

1. **Start Backend**
   ```bash
   cd backend
   python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend**
   ```bash
   cd frontend/flowstate
   npm run dev
   ```

3. **Access Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Debugging

#### Backend Debugging
```bash
# Run with verbose logging
cd backend
python -m uvicorn app:app --reload --log-level debug

# Debug specific test
python -m pytest tests/test_app.py::test_health_endpoint -v -s
```

#### Frontend Debugging
```bash
# Run with debug mode
cd frontend/flowstate
npm run dev

# Debug tests
npm test -- --verbose --no-cache
```

### Common Development Tasks

#### Adding a New API Endpoint
1. Add endpoint to `backend/app.py`
2. Create test in `backend/tests/test_app.py`
3. Update API documentation
4. Test manually and with automated tests

#### Adding a New React Component
1. Create component in `frontend/flowstate/src/components/`
2. Create test in `frontend/flowstate/src/tests/`
3. Export from appropriate index file
4. Add to style guide if needed

#### Adding Dependencies

**Backend:**
```bash
cd backend
pip install new-package
pip freeze > requirements.txt
```

**Frontend:**
```bash
cd frontend/flowstate
npm install new-package
```

### Project Structure

```
flowstate/
├── .github/workflows/     # CI/CD configuration
├── backend/              # Python FastAPI backend
│   ├── agents/          # LangGraph agents
│   ├── models/          # Database models
│   ├── tests/           # Backend tests
│   ├── utils/           # Utility functions
│   ├── app.py           # Main FastAPI app
│   └── requirements*.txt # Dependencies
├── frontend/flowstate/   # Next.js frontend
│   ├── src/
│   │   ├── app/         # Next.js app directory
│   │   ├── components/  # React components
│   │   ├── tests/       # Frontend tests
│   │   └── utils/       # Frontend utilities
│   ├── package.json     # Frontend dependencies
│   └── jest.config.cjs  # Test configuration
└── TESTING.md           # Testing documentation
```

### Getting Help

- **Documentation**: Check `TESTING.md` for detailed testing guide
- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub discussions for questions
- **Code Review**: Ask for help in pull request comments

### Performance Guidelines

- Keep PR sizes reasonable (< 1000 lines changed)
- Write efficient database queries
- Optimize frontend bundle size
- Add performance tests for critical paths
- Monitor CI/CD pipeline performance

### Security Guidelines

- Never commit secrets or API keys
- Use environment variables for configuration
- Follow OWASP security guidelines
- Run security scans regularly
- Update dependencies promptly

## Ready to Contribute?

1. Fork the repository
2. Follow the development setup above
3. Create your feature branch
4. Make your changes with tests
5. Submit a pull request

Thank you for contributing to FlowState! 🚀