"""Simplified tests that don't require external dependencies."""
import pytest
import os
import sys

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.unit
def test_environment_setup():
    """Test that test environment is properly configured."""
    assert os.getenv("ENV") == "test"
    assert os.getenv("DATABASE_URL") is not None
    assert os.getenv("SECRET_KEY") is not None


@pytest.mark.unit
def test_python_version():
    """Test that we're running on a supported Python version."""
    assert sys.version_info >= (3, 8)


@pytest.mark.unit
def test_file_structure():
    """Test that required files exist."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check for main application files
    assert os.path.exists(os.path.join(backend_dir, "app.py"))
    assert os.path.exists(os.path.join(backend_dir, "requirements.txt"))
    assert os.path.exists(os.path.join(backend_dir, "Dockerfile"))
    
    # Check for agent files
    agents_dir = os.path.join(backend_dir, "agents")
    assert os.path.exists(agents_dir)
    assert os.path.exists(os.path.join(agents_dir, "supervisor.py"))
    assert os.path.exists(os.path.join(agents_dir, "response.py"))


@pytest.mark.unit
def test_imports():
    """Test that we can import basic Python modules."""
    try:
        import json
        import uuid
        import datetime
        import asyncio
        
        assert json is not None
        assert uuid is not None
        assert datetime is not None
        assert asyncio is not None
        
    except ImportError as e:
        pytest.fail(f"Failed to import basic modules: {e}")


@pytest.mark.unit
def test_agent_files_exist():
    """Test that agent files exist and can be read."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Test agent files
    agent_files = [
        "agents/supervisor.py",
        "agents/response.py", 
        "agents/project_manager.py",
        "agents/configuration.py"
    ]
    
    for agent_file in agent_files:
        file_path = os.path.join(backend_dir, agent_file)
        assert os.path.exists(file_path), f"Agent file {agent_file} does not exist"
        
        # Check that file is readable and has content
        with open(file_path, 'r') as f:
            content = f.read()
            assert len(content) > 0, f"Agent file {agent_file} is empty"


@pytest.mark.unit
def test_response_agent_prompt():
    """Test that response agent has a prompt defined."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    response_file = os.path.join(backend_dir, "agents", "response.py")
    
    with open(response_file, 'r') as f:
        content = f.read()
        
    # Check for prompt definition
    assert "response_prompt" in content
    assert "jsx" in content.lower() or "react" in content.lower()


@pytest.mark.unit
def test_configuration_files():
    """Test that configuration files exist."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    config_files = [
        "requirements.txt",
        "Dockerfile",
        "pyproject.toml"
    ]
    
    for config_file in config_files:
        file_path = os.path.join(backend_dir, config_file)
        assert os.path.exists(file_path), f"Configuration file {config_file} does not exist"


@pytest.mark.unit
def test_docker_configuration():
    """Test that Dockerfile is properly configured."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dockerfile_path = os.path.join(backend_dir, "Dockerfile")
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Check for key Dockerfile components
    assert "FROM python" in content
    assert "COPY requirements.txt" in content
    assert "RUN pip install" in content
    assert "uvicorn" in content or "gunicorn" in content


@pytest.mark.unit
def test_utility_files():
    """Test that utility files exist."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check for utility directories and files
    utils_dir = os.path.join(backend_dir, "utils")
    if os.path.exists(utils_dir):
        # If utils directory exists, check for common files
        assert os.path.isdir(utils_dir)
    
    # Check for database files
    assert os.path.exists(os.path.join(backend_dir, "db.py"))
    
    # Check for model files
    models_dir = os.path.join(backend_dir, "models")
    if os.path.exists(models_dir):
        assert os.path.isdir(models_dir)


@pytest.mark.unit
def test_requirements_file():
    """Test that requirements.txt has essential packages."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    requirements_path = os.path.join(backend_dir, "requirements.txt")
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    # Check for essential packages
    essential_packages = ["fastapi", "uvicorn", "pydantic"]
    for package in essential_packages:
        assert package in content.lower(), f"Essential package {package} not found in requirements.txt"


@pytest.mark.integration
def test_project_structure():
    """Test overall project structure."""
    # Get to the root of the project
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(backend_dir)
    
    # Check for main project components
    assert os.path.exists(os.path.join(project_root, "backend"))
    assert os.path.exists(os.path.join(project_root, "frontend"))
    
    # Check for frontend structure
    frontend_dir = os.path.join(project_root, "frontend", "flowstate")
    if os.path.exists(frontend_dir):
        assert os.path.exists(os.path.join(frontend_dir, "package.json"))
        assert os.path.exists(os.path.join(frontend_dir, "src"))


@pytest.mark.unit
def test_env_variables_for_testing():
    """Test that environment variables are set correctly for testing."""
    # Test environment
    assert os.getenv("ENV") == "test"
    
    # Database URL should be test-friendly
    db_url = os.getenv("DATABASE_URL", "")
    assert "test" in db_url.lower() or "sqlite" in db_url.lower()
    
    # Secret key should be set
    secret_key = os.getenv("SECRET_KEY")
    assert secret_key is not None
    assert len(secret_key) > 0