from pathlib import Path

import pytest

from tidylake.core.context import get_or_create_context


@pytest.fixture(autouse=True)
def auto_reset(reset_context_instance):
    """Automatically reset context instance for all tests in this module."""
    pass


def test_config_loads_with_relative_path_from_different_directory():
    """Test that config can load config file with relative data_product paths from any directory."""
    # Given - we're in the project root, not in the demo directory
    config_file = "src/tidylake/demo/pandas_local/tidylake.yml"

    # When
    context_instance = get_or_create_context(config_file)
    data_products = context_instance.get_graph_sequence()

    # Then
    assert context_instance.name == "Test Pandas Local"
    assert data_products == [
        "bronze_customers",
        "bronze_profile",
        "silver_customers",
        "gold_customers",
    ]


def test_context_loads_with_absolute_path():
    """Test that config can load config file with absolute path."""
    # Given
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    config_file = str(demo_path / "tidylake.yml")

    # When
    context_instance = get_or_create_context(config_file)
    data_products = context_instance.get_graph_sequence()

    # Then
    assert context_instance.name == "Test Pandas Local"
    assert data_products == [
        "bronze_customers",
        "bronze_profile",
        "silver_customers",
        "gold_customers",
    ]
