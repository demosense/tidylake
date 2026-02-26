import subprocess


def test_cli_help_command():
    """Test CLI help command works."""
    result = subprocess.run(["uv", "run", "tidylake", "--help"], capture_output=True, text=True)

    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_cli_list_without_config(tmp_path, monkeypatch):
    """Test CLI list command fails gracefully without config."""
    monkeypatch.chdir(tmp_path)

    result = subprocess.run(["uv", "run", "tidylake", "list"], capture_output=True, text=True)

    # Should fail gracefully when no tidylake.yml exists
    assert result.returncode != 0
