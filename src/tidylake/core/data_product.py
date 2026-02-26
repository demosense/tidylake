import functools
import importlib
import sys
from collections.abc import Callable
from pathlib import Path

import yaml

from tidylake.plugins.compute_engine import ComputeEnginePlugin
from tidylake.utils.code_parser import parse_script_inputs

from .commons import EXECUTION_MODE_INTERACTIVE, execution_mode, get_use_synthetic_data


class DataProduct:
    """
    The Data Product class is one of the building blocks of tidylake.

    This class is meant to be instantiated from the manifest files when loading the framework,
    objects will be retrieved using the available helper functions in the scripts.
    """

    name: str
    schema: dict = None
    raw_inputs: list[str]
    inputs: list[str]
    script: str = None
    sink: Callable = None
    # TODO: how can we type this as it depends on the compute engine or can be even custom...
    output_data = None
    compute_engine: ComputeEnginePlugin = None

    @classmethod
    def get_config(cls, config_file: str) -> dict:
        config_file_path = Path(config_file).resolve()
        if not config_file_path.is_file():
            raise FileNotFoundError(f"Configuration file {config_file_path!r} not found.")

        # Create data producct
        with open(config_file_path) as data_product_config_file:
            data_product_config = yaml.safe_load(data_product_config_file)

        # TODO: Validate data_product config
        return data_product_config

    def __init__(
        self,
        name: str,
        schema: dict,
        script: str | None = None,
        config_dir: Path | None = None,
    ):
        self.name = name
        self.schema = schema
        self.script = script if script is not None else name
        self.config_dir = config_dir or Path(".")

        self.raw_inputs = []
        self.inputs = []

        # process script with ast to analyze inputs
        script_path = self.config_dir / f"{self.script.replace('.', '/')}.py"

        if script_path.is_file():
            try:
                with open(script_path) as f:
                    code = f.read()
                self.inputs = parse_script_inputs(code)
            except FileNotFoundError:
                print(f"WARNING: Data product script {self.script} not found. Inputs will not be available.")
        # No warning if script file doesn't exist - it's optional

    def set_compute_engine(self, compute_engine: ComputeEnginePlugin):
        """
        Set the compute engine for the data product.

        Args:
            compute_engine (ComputeEnginePlugin): The compute engine plugin to use.
        """
        self.compute_engine = compute_engine

    # noqa: SIM108
    def read_input(self, name: str):
        if not self.compute_engine:
            raise ValueError("Compute engine not set for the data product.")

        if get_use_synthetic_data():
            result = self.compute_engine.read_synthetic_dataset(self.schema)
        else:
            result = self.compute_engine.read_dataset(name)

        # if running in interactive mode, display the result
        if execution_mode == EXECUTION_MODE_INTERACTIVE:
            if self.compute_engine:
                self.compute_engine.display_dataset(result)
            else:
                display(result)  # pyright: ignore[reportUndefinedVariable] # noqa: F821

        return result

    def add_input(self, name: str | None = None, raw: bool = False) -> Callable[[Callable], Callable]:
        """
        Decorator to add an input to the data product within the script.

        Args:
            name (str, optional): The name of the input. If not provided, the function
                name will be used.
            raw (bool, optional): If True, the input is considered a raw input.
                Defaults to False.

        Returns:
            Callable: A decorator that wraps the function to add it as an input,
                calling the function will return the DataFrame or data structure

        """

        def decorator(fn: Callable):
            input_name = name or fn.__name__
            if not isinstance(input_name, str):
                raise ValueError("Input name must be a string.")

            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                # invoke the function to get the DataFrame or data structure
                result = fn(*args, **kwargs)

                if execution_mode == EXECUTION_MODE_INTERACTIVE:
                    if self.compute_engine:
                        self.compute_engine.display_dataset(result)
                    else:
                        display(result)  # pyright: ignore[reportUndefinedVariable] # noqa: F821

                return result

            return wrapped

        return decorator

    def peek(self) -> None:
        if self.compute_engine:
            df = self.read_input(self.name)
            self.compute_engine.display_dataset(df)
        else:
            raise ValueError("Compute engine not set for the data product.")

    def set_sink(
        self,
    ) -> Callable[[Callable], Callable]:
        def decorator(fn: Callable):
            self.sink = fn

            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                print("WARN: Calling sink from data product modules has no effect")

            return wrapped

        return decorator

    def set_output_data(self, data):
        if not self.compute_engine:
            raise ValueError("Compute engine not set for the data product.")

        self.compute_engine.validate_dataset_schema(self.schema, data)
        self.output_data = data

    def get_schemas(self):
        catalog_schema = None

        if self.compute_engine and self.compute_engine.check_catalog_exists(self.name):
            catalog_schema = self.compute_engine.get_schema_from_catalog(self.name)

        return {
            "defined_schema": self.schema,
            "catalog_schema": catalog_schema if catalog_schema else {},
        }

    def update_or_create_schema(self, commit: bool = False) -> None:
        if self.compute_engine and self.schema:
            self.compute_engine.update_or_create_schema(self.name, self.schema, commit=commit)
        else:
            raise ValueError(
                "Compute engine or schema not set for the data product.Cannot update or create schema."
            )

    def run(self):
        # If session is interactive do nothing
        if execution_mode == EXECUTION_MODE_INTERACTIVE:
            print("WARN: Calling run from data product modules has no effect")
            return

        else:
            # Ensure the directory containing your modules is in sys.path
            project_root = str(self.config_dir.resolve())

            sys.path.insert(0, project_root)
            importlib.import_module(self.script)

            if self.sink:
                self.sink()

            elif self.compute_engine:
                if self.output_data is None:
                    raise ValueError(
                        "No output data set for the data product.\
                                     Please set output_data when using a compute engine."
                    )

                self.compute_engine.write_dataset(
                    self.name,
                    self.output_data,
                )
            else:
                raise ValueError("No compute engine or set set for the data product.")
