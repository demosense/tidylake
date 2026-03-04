import subprocess
from pathlib import Path


def test_cli_run_downstream(monkeypatch):
    """Test CLI run --downstream using demo pandas_local"""
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    monkeypatch.chdir(demo_path)

    result = subprocess.run(
        [
            "uv",
            "run",
            "tidylake",
            "run",
            "--data-product",
            "silver_customers",
            "--downstream",
        ],
        capture_output=True,
        text=True,
        cwd=demo_path,
    )

    assert result.returncode == 0
    assert "Running data product: silver_customers" in result.stdout
    assert "Running data product: gold_customers" in result.stdout
    assert "Running data product: bronze_customers" not in result.stdout
    assert "Running data product: bronze_profile" not in result.stdout


def test_cli_run_upstream(monkeypatch):
    """Test CLI run --upstream using demo pandas_local"""
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    monkeypatch.chdir(demo_path)

    result = subprocess.run(
        [
            "uv",
            "run",
            "tidylake",
            "run",
            "--data-product",
            "silver_customers",
            "--upstream",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Running data product: bronze_customers" in result.stdout
    assert "Running data product: bronze_profile" in result.stdout
    assert "Running data product: silver_customers" in result.stdout
    assert "Running data product: gold_customers" not in result.stdout


def test_cli_run_single(monkeypatch):
    """Test CLI run single data product using demo pandas_local"""
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    monkeypatch.chdir(demo_path)

    result = subprocess.run(
        ["uv", "run", "tidylake", "run", "--data-product", "silver_customers"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Running data product: silver_customers" in result.stdout
    assert "Running data product: bronze_profile" not in result.stdout
    assert "Running data product: bronze_customers" not in result.stdout
    assert "Running data product: gold_customers" not in result.stdout


def test_cli_run_all(monkeypatch):
    """Test CLI run all data products using demo pandas_local"""
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    monkeypatch.chdir(demo_path)

    result = subprocess.run(
        ["uv", "run", "tidylake", "run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Running data product: bronze_profile" in result.stdout
    assert "Running data product: bronze_customers" in result.stdout
    assert "Running data product: silver_customers" in result.stdout
    assert "Running data product: gold_customers" in result.stdout


def test_cli_run_upstream_downstream_fail(monkeypatch):
    """Test CLI run fails with --upstream and --downstream using demo pandas_local"""
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    monkeypatch.chdir(demo_path)

    result = subprocess.run(
        [
            "uv",
            "run",
            "tidylake",
            "run",
            "--data-product",
            "silver_customers_orders",
            "--upstream",
            "--downstream",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "mutually exclusive" in result.stderr


def test_cli_run_upstream_fail(monkeypatch):
    """Test CLI run fails with --upstream without --data-product using demo pandas_local"""
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    monkeypatch.chdir(demo_path)

    result = subprocess.run(
        ["uv", "run", "tidylake", "run", "--upstream"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "requires --data-product" in result.stderr


def test_cli_run_downstream_fail(monkeypatch):
    """Test CLI run fails with --downstream without --data-product using demo pandas_local"""
    demo_path = Path(__file__).parent.parent.parent / "src" / "tidylake" / "demo" / "pandas_local"
    monkeypatch.chdir(demo_path)

    result = subprocess.run(
        ["uv", "run", "tidylake", "run", "--downstream"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "requires --data-product" in result.stderr
