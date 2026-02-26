"""Project scaffolding functionality for creating new projects."""

import shutil
from pathlib import Path


def get_demo_path(engine: str) -> Path:
    """Get path to demo directory for specified engine."""
    demo_map = {
        "pandas": "pandas_local",
        "spark": "spark",
        "iceberg": "pandas_iceberg_local",
    }

    if engine not in demo_map:
        raise ValueError(f"Unknown engine: {engine}. Available: {list(demo_map.keys())}")

    demo_dir = Path(__file__).parent.parent / "demo" / demo_map[engine]

    if not demo_dir.exists():
        raise FileNotFoundError(f"Demo directory not found: {demo_dir}")

    return demo_dir


def create_project_structure(project_name: str, target_dir: Path, engine: str = "pandas") -> None:
    """Create complete project structure by copying from demo."""
    project_dir = target_dir / project_name

    if project_dir.exists():
        raise FileExistsError(f"Directory '{project_name}' already exists")

    # Get demo directory
    demo_dir = get_demo_path(engine)

    # Copy entire demo directory
    shutil.copytree(demo_dir, project_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # Update project name in tidylake.yml
    context_config_path = project_dir / "tidylake.yml"
    if context_config_path.exists():
        content = context_config_path.read_text()
        # Replace the demo name with project name
        content = content.replace("Test Pandas Local", project_name)
        content = content.replace("Test Spark", project_name)
        content = content.replace("Test Pandas Iceberg Local", project_name)
        context_config_path.write_text(content)
