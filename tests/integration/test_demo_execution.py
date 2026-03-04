"""Integration tests for demo pipeline execution."""

from pathlib import Path

import pytest

from tidylake.core.context import get_or_create_context


@pytest.fixture(autouse=True)
def auto_reset(reset_context_instance):
    """Automatically reset context instance for all tests in this module."""
    pass


def test_pandas_local_demo_runs_successfully(monkeypatch, tmp_path):
    """Test that pandas_local demo executes without errors."""
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    monkeypatch.chdir(demo_path)

    context_instance = get_or_create_context("tidylake.yml")

    # Run the pipeline
    context_instance.run(name=None)

    # Verify all data_products were added
    assert len(context_instance.data_products) == 4
    assert "bronze_customers" in context_instance.data_products
    assert "bronze_profile" in context_instance.data_products
    assert "silver_customers" in context_instance.data_products
    assert "gold_customers" in context_instance.data_products


def test_pandas_iceberg_local_demo_runs_successfully(monkeypatch, tmp_path):
    """Test that pandas_iceberg_local demo executes without errors."""
    import sys

    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_iceberg_local"
    monkeypatch.chdir(demo_path)

    # Clear module cache to ensure scripts re-execute
    for mod in list(sys.modules.keys()):
        if "bronze_customers" in mod or "silver_customers" in mod:
            del sys.modules[mod]

    context_instance = get_or_create_context("tidylake.yml")

    # Create schemas first (required for Iceberg)
    context_instance.schema_update(commit=True)

    # Run the pipeline
    context_instance.run(name=None)

    # Verify all data_products were added
    assert len(context_instance.data_products) == 2
    assert "bronze_customers" in context_instance.data_products
    assert "silver_customers" in context_instance.data_products
