from pathlib import Path

import pytest

from tidylake.core.context import get_or_create_context


@pytest.fixture(autouse=True)
def auto_reset(reset_context_instance):
    """Automatically reset context instance for all tests in this module."""
    pass


def test_bootstrap_pandas_local(monkeypatch):
    # Given
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    monkeypatch.chdir(demo_path)
    config_file = "tidylake.yml"

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


def test_bootstrap_pandas_iceberg_local(monkeypatch):
    # Given
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_iceberg_local"
    monkeypatch.chdir(demo_path)
    config_file = "tidylake.yml"

    # When
    context_instance = get_or_create_context(config_file)
    data_products = context_instance.get_graph_sequence()

    # Then
    assert context_instance.name == "Test Pandas Iceberg Local"
    assert data_products == [
        "bronze_customers",
        "silver_customers",
    ]
