"""CLI command implementations."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tidylake.core import get_or_create_context
from tidylake.scaffold import create_project_structure

console = Console()


def version_callback(value: bool):
    """Callback for --version flag.

    Args:
        value: Whether --version flag was provided.
    """
    if value:
        from importlib.metadata import version as get_version

        pkg_version = get_version("tidylake")
        console.print(f"[bold cyan]tidylake[/bold cyan] version [green]{pkg_version}[/green]")
        raise typer.Exit()


app = typer.Typer(pretty_exceptions_enable=False)
app_schema = typer.Typer(pretty_exceptions_enable=False)
app.add_typer(app_schema, name="schema", help="Schema related commands")

OPTION_FILE = typer.Option("tidylake.yml", help="Path to the YAML file defining processes")


def create_context_from_config(config_file: str):
    context = get_or_create_context(config_file)
    return context


@app.command()
def list(
    file: str | None = OPTION_FILE,
    mermaid: bool = typer.Option(False, "--mermaid", help="Generate Mermaid diagram"),
    textual: bool = typer.Option(False, "--textual", help="Open Textual viewer"),
):
    """Display pipeline structure and visualization.

    Args:
        file: Path to the configuration YAML file.
        mermaid: Generate Mermaid diagram output.
        textual: Launch interactive terminal UI viewer.
    """
    selected_modes = [mermaid, textual]
    if sum(bool(mode) for mode in selected_modes) > 1:
        raise typer.BadParameter("Mermaid and Textual modes are mutually exclusive. Choose one.")

    context = create_context_from_config(file)
    context.visualize(mermaid=mermaid, textual=textual)


@app.command()
def run(
    file: str | None = OPTION_FILE,
    data_product: str | None = typer.Option(None, help="Specific data product to run"),
    continue_run: bool | None = typer.Option(False, help="Continue from the last data product"),
):
    """Execute pipeline or individual data product.

    Args:
        file: Path to the configuration YAML file.
        data product: Name of specific data product to execute. If None, runs entire pipeline.
        continue_run: Continue execution from the last completed data product.
    """
    context = create_context_from_config(file)
    context.run(name=data_product, continue_run=continue_run)


@app.command()
def peek(
    file: str | None = OPTION_FILE,
    data_product: str | None = typer.Option(None, help="Specific data product to run"),
):
    """Preview data product output data without executing the pipeline.

    Args:
        file: Path to the configuration YAML file.
        data_product: Name of specific data product to preview.
    """
    context = create_context_from_config(file)
    context.peek_data_product(name=data_product)


@app_schema.command()
def diff(
    file: str | None = OPTION_FILE,
    data_product: str | None = typer.Option(None, help="Specific data product to check"),
):
    """Show schema differences between defined and catalog schemas.

    Args:
        file: Path to the configuration YAML file.
        data_product: Name of specific data product to check. If None, checks all data products.
    """
    context = create_context_from_config(file)
    result = context.schema_diff(name=data_product)

    def print_schema_table(data_product_name, schema_diff):
        table = Table(title=data_product_name)
        table.add_column("column")
        table.add_column("defined_schema")
        table.add_column("catalog_schema")
        table.add_column("status")

        defined_schema_props = schema_diff.get("defined_schema", {}).get("properties", {})
        catalog_schema_props = schema_diff.get("catalog_schema", {}).get("properties", {})

        all_keys = defined_schema_props.keys() | catalog_schema_props.keys()
        for col in all_keys:
            def_type = defined_schema_props.get(col, {}).get("type", "<missing>")
            cat_type = catalog_schema_props.get(col, {}).get("type", "<missing>")
            if def_type == cat_type:
                status = "[green]OK[/green]"
            elif cat_type == "<missing>":
                status = "[yellow]ADD[/yellow]"
            elif def_type == "<missing>":
                status = "[blue]DROP[/blue]"
            else:
                status = "[red]ALTER[/red]"
            table.add_row(*(col, def_type, cat_type, status))

        console.print(table)

    for data_product_name, schema_diff in result.items():
        print_schema_table(data_product_name, schema_diff)


@app_schema.command()
def update(
    file: str | None = OPTION_FILE,
    data_product: str | None = typer.Option(None, help="Specific data product to update"),
    commit: bool | None = typer.Option(False, help="Commit changes"),
):
    """Update schema definitions to match catalog schemas.

    Args:
        file: Path to the configuration YAML file.
        data_product: Name of specific data product to update. If None, updates all data products.
        commit: Apply changes to schema files. If False, runs in dry-run mode.
    """
    context = create_context_from_config(file)
    context.schema_update(name=data_product, commit=commit)


@app.command()
def init(
    name: str = typer.Option("my_tidylake_project", "--name", help="Project name"),
    engine: str = typer.Option("pandas", "--engine", help="Engine type: pandas, spark, iceberg"),
):
    """Initialize a new project from demo template."""
    try:
        create_project_structure(name, Path.cwd(), engine=engine)
        console.print(f"✨ Created project: {name}")
        console.print(f"🔧 Engine: {engine}")
        console.print(f"\n📁 Project copied from demo/{engine}")
        console.print("\n🚀 Get started:")
        console.print(f"  cd {name}")
        console.print("  tidylake list")
        console.print("  tidylake run")
    except (FileExistsError, ValueError, FileNotFoundError) as e:
        console.print(f"❌ Error: {e}")
        raise typer.Exit(code=1) from None


@app.command()
def version():
    """Show version information."""
    from importlib.metadata import version as get_version

    pkg_version = get_version("tidylake")
    console.print(f"[bold cyan]tidylake[/bold cyan] version [green]{pkg_version}[/green]")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """tidylake CLI

    Args:
        ctx: Typer context.
        version: Show version flag.
    """
