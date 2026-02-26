from unittest.mock import Mock

import pytest

import tidylake.core.context as context_module


@pytest.fixture
def temp_workspace(tmp_path, monkeypatch):
    """
    Provide a temporary working directory and ensure CWD/env vars point there.

    Returns:
        Path: The temporary workspace directory.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TIDYLAKE_TEMP_WORKSPACE", str(tmp_path))
    return tmp_path


@pytest.fixture
def set_env(monkeypatch):
    """
    Helper fixture to set or unset environment variables within a test.
    """

    def _set_env(**env):
        for key, value in env.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, str(value))

    return _set_env


@pytest.fixture
def mock_data_product():
    """Create a mock data_product for testing."""
    data_product = Mock()
    data_product.name = "test_data_product"
    data_product.inputs = []
    data_product.schema = {}
    return data_product


@pytest.fixture
def sample_context_config(tmp_path):
    """Create sample tidylake configuration file."""
    config_content = """
tidylake:
  name: Test project
  include_data_products:
    - test_data_product.yml
"""
    config_file = tmp_path / "tidylake.yml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def reset_context_instance():
    """Reset the context singleton instance before and after each test.

    This fixture ensures test isolation by clearing the global context instance
    that is created by get_or_create_context(). Without this, tests that create
    context instances would interfere with each other.

    Usage:
        Use as autouse=True in test files that need automatic reset:

        @pytest.fixture(autouse=True)
        def auto_reset(reset_context_instance):
            pass
    """
    context_module.context = None
    yield
    context_module.context = None
