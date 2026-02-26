"""Integration tests for init CLI command."""

import os

import yaml
from typer.testing import CliRunner

from tidylake.cli.commands import app

runner = CliRunner()


def test_init_command_creates_project(tmp_path):
    """Test init command creates project structure."""
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--name", "my_project"])
        assert result.exit_code == 0
        assert "Created project: my_project" in result.stdout

        project_dir = tmp_path / "my_project"
        assert project_dir.exists()
        assert (project_dir / "tidylake.yml").exists()
    finally:
        os.chdir(original_dir)


def test_init_command_default_name(tmp_path):
    """Test init command with default project name."""
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        project_dir = tmp_path / "my_tidylake_project"
        assert project_dir.exists()
    finally:
        os.chdir(original_dir)


def test_init_command_fails_if_exists(tmp_path):
    """Test init command fails if directory exists."""
    original_dir = os.getcwd()
    try:
        project_dir = tmp_path / "existing_project"
        project_dir.mkdir()

        os.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--name", "existing_project"])
        assert result.exit_code != 0
        assert "already exists" in result.stdout
    finally:
        os.chdir(original_dir)


def test_generated_project_has_valid_yaml(tmp_path):
    """Test generated YAML files are valid."""
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        runner.invoke(app, ["init", "--name", "test_project"])

        project_dir = tmp_path / "test_project"
        context_config = yaml.safe_load((project_dir / "tidylake.yml").read_text())
        assert context_config["tidylake"]["name"] == "test_project"
        assert "include_data_products" in context_config["tidylake"]

        bronze_config = yaml.safe_load((project_dir / "bronze_customers.yml").read_text())
        assert bronze_config["data_product"]["name"] == "bronze_customers"
    finally:
        os.chdir(original_dir)


def test_init_command_with_engine(tmp_path):
    """Test init command with different engines."""
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--name", "spark_project", "--engine", "spark"])
        assert result.exit_code == 0
        assert "spark" in result.stdout

        project_dir = tmp_path / "spark_project"
        assert project_dir.exists()
    finally:
        os.chdir(original_dir)
