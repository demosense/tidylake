"""Acceptance tests for init command end-to-end workflow."""

import subprocess


def test_init_list_workflow(tmp_path):
    """Test workflow: init -> list."""
    project_name = "demo_project"

    # data_product 1: Initialize project
    result = subprocess.run(
        ["uv", "run", "tidylake", "init", "--name", project_name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Created project" in result.stdout

    project_dir = tmp_path / project_name

    # Verify structure (pandas demo structure)
    assert (project_dir / "tidylake.yml").exists()
    assert (project_dir / "bronze_customers.py").exists()
    assert (project_dir / "silver_customers.py").exists()
    assert (project_dir / "gold_customers.py").exists()

    # data_product 2: List pipeline
    result = subprocess.run(
        ["uv", "run", "tidylake", "list"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "bronze_customers" in result.stdout
    assert "silver_customers" in result.stdout
    assert "gold_customers" in result.stdout
