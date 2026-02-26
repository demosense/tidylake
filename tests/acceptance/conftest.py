import os
import subprocess
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def acceptance_workspace(tmp_path):
    """
    Create an isolated workspace with a minimal two-step pipeline.
    """

    workspace = tmp_path / "workspace"
    data_products_dir = workspace / "data_products"

    data_products_dir.mkdir(parents=True)

    # Bronze data_product: writes a simple text artifact.
    bronze_script = textwrap.dedent(
        """
        from pathlib import Path
        from tidylake.core.context import get_or_create_context

        data_product = get_or_create_context().get_data_product("bronze")
        OUTPUT_FILE = Path("bronze.txt")


        @data_product.set_sink()
        def write_bronze():
            OUTPUT_FILE.write_text("bronze data")
        """
    )

    # Silver data_product: depends on bronze output and transforms it.
    silver_script = textwrap.dedent(
        """
        from pathlib import Path
        from tidylake.core.context import get_or_create_context

        data_product = get_or_create_context().get_data_product("silver")


        @data_product.add_input()
        def bronze():
            return Path("bronze.txt").read_text()


        CONTENT = bronze()


        @data_product.set_sink()
        def write_silver():
            Path("silver.txt").write_text(CONTENT.upper())
        """
    )

    (data_products_dir / "bronze_data_product.py").write_text(bronze_script)
    (data_products_dir / "silver_data_product.py").write_text(silver_script)

    (data_products_dir / "bronze.yml").write_text(
        textwrap.dedent(
            """
            data_product:
              name: bronze
              script: data_products.bronze_data_product
            """
        ).strip()
    )

    (data_products_dir / "silver.yml").write_text(
        textwrap.dedent(
            """
            data_product:
              name: silver
              script: data_products.silver_data_product
            """
        ).strip()
    )

    (workspace / "tidylake.yml").write_text(
        textwrap.dedent(
            """
            tidylake:
              name: Acceptance Pipeline
              include_data_products:
                - data_products/bronze.yml
                - data_products/silver.yml
            """
        ).strip()
    )

    return workspace


@pytest.fixture
def cli_runner():
    """
    Run tidylake commands via uv ensuring a dedicated cache per workspace.
    """

    def _run(args, cwd: Path, check=True):
        env = os.environ.copy()
        cache_dir = Path(cwd) / ".uv-cache"
        cache_dir.mkdir(exist_ok=True)

        env.setdefault("UV_CACHE_DIR", str(cache_dir))

        return subprocess.run(
            ["uv", "run", "tidylake", *args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=check,
        )

    return _run
