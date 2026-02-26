"""Unit tests for project scaffolding functionality."""

import pytest

from tidylake.scaffold import create_project_structure, get_demo_path


def test_get_demo_path_pandas():
    """Test getting pandas demo path."""
    path = get_demo_path("pandas")
    assert path.exists()
    assert path.name == "pandas_local"


def test_get_demo_path_spark():
    """Test getting spark demo path."""
    path = get_demo_path("spark")
    assert path.exists()
    assert path.name == "spark"


def test_get_demo_path_iceberg():
    """Test getting iceberg demo path."""
    path = get_demo_path("iceberg")
    assert path.exists()
    assert path.name == "pandas_iceberg_local"


def test_get_demo_path_invalid():
    """Test invalid engine raises error."""
    with pytest.raises(ValueError, match="Unknown engine"):
        get_demo_path("invalid_engine")


def test_create_project_structure_pandas(tmp_path):
    """Test pandas project structure creation."""
    project_name = "test_tidylake"
    create_project_structure(project_name, tmp_path, engine="pandas")

    project_dir = tmp_path / project_name
    assert project_dir.exists()
    assert (project_dir / "tidylake.yml").exists()
    assert (project_dir / "bronze_customers.yml").exists()
    assert (project_dir / "bronze_customers.py").exists()
    assert (project_dir / "silver_customers.yml").exists()
    assert (project_dir / "gold_customers.yml").exists()


def test_create_project_structure_spark(tmp_path):
    """Test spark project structure creation."""
    project_name = "test_spark"
    create_project_structure(project_name, tmp_path, engine="spark")

    project_dir = tmp_path / project_name
    assert project_dir.exists()
    assert (project_dir / "tidylake.yml").exists()


def test_create_project_structure_fails_if_exists(tmp_path):
    """Test that creation fails if directory already exists."""
    project_name = "test_tidylake"
    project_dir = tmp_path / project_name
    project_dir.mkdir()

    with pytest.raises(FileExistsError, match="already exists"):
        create_project_structure(project_name, tmp_path, engine="pandas")


def test_create_project_structure_invalid_engine(tmp_path):
    """Test that invalid engine raises error."""
    with pytest.raises(ValueError, match="Unknown engine"):
        create_project_structure("test", tmp_path, engine="invalid")
