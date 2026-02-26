from pathlib import Path


def test_cli_list_shows_data_products(acceptance_workspace, cli_runner):
    result = cli_runner(["list"], cwd=acceptance_workspace)

    assert result.returncode == 0
    assert "bronze" in result.stdout
    assert "silver" in result.stdout


def test_cli_mermaid_output(acceptance_workspace, cli_runner):
    result = cli_runner(["list", "--mermaid"], cwd=acceptance_workspace)

    assert result.returncode == 0
    assert "```mermaid" in result.stdout
    assert "flowchart TD" in result.stdout


def test_cli_run_full_pipeline(acceptance_workspace, cli_runner):
    result = cli_runner(["run"], cwd=acceptance_workspace)
    assert result.returncode == 0

    bronze = Path(acceptance_workspace / "bronze.txt")
    silver = Path(acceptance_workspace / "silver.txt")

    assert bronze.exists()
    assert silver.exists()
    assert silver.read_text() == bronze.read_text().upper()


def test_cli_run_single_data_product(acceptance_workspace, cli_runner):
    result = cli_runner(["run", "--data-product", "bronze"], cwd=acceptance_workspace)
    assert result.returncode == 0

    bronze = Path(acceptance_workspace / "bronze.txt")
    silver = Path(acceptance_workspace / "silver.txt")

    assert bronze.exists()
    assert not silver.exists()
