import importlib
import re
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

import yaml

from tidylake.plugins.compute_engine import ComputeEnginePlugin

from .commons import DEFAULT_CONFIG_FILE
from .data_product import DataProduct

context = None


class TidyLakeContext:
    @classmethod
    def get_config(cls, config_file: str) -> dict:
        """
        Load the configuration from a YAML file.

        Args:
            config_file (str): The path to the configuration file.

        Returns:
            dict: The loaded configuration.
        """

        config_file_path = Path(config_file).resolve()
        if not config_file_path.is_file():
            raise FileNotFoundError(f"Configuration file {config_file_path!r} not found.")

        with open(config_file_path) as f:
            context_config = yaml.safe_load(f)

        # TODO: Validate context config data
        return context_config

    @classmethod
    def load_plugin(cls, plugin_name: str, plugin_config: dict, config_dir: Path = None) -> None:
        """
        Load a  plugin dynamically.

        Args:
            plugin_config (dict): The configuration for the plugin.
            config_dir (Path): Directory to resolve relative plugin paths from.
        """

        pluging_class_name = plugin_config.get("plugin_class_name")

        if not pluging_class_name:
            raise ValueError(f"{plugin_name} configuration must include 'plugin_class_name'.")

        # If the plugin is specified as a module
        if plugin_config.get("plugin_module"):
            module = importlib.import_module(plugin_config.get("plugin_module"))

            return getattr(module, pluging_class_name)(plugin_config)

        # If the plugin is specified as a file path
        elif plugin_config.get("plugin_path"):
            plugin_path = plugin_config.get("plugin_path")
            if config_dir and not Path(plugin_path).is_absolute():
                file_path = (config_dir / plugin_path).resolve()
            else:
                file_path = Path(plugin_path).resolve()

            spec = importlib.util.spec_from_file_location(plugin_name, file_path)

            if spec is None:
                raise ImportError(
                    f"Could not find {plugin_name} plugin module at {file_path!r}. \
                                  Please check the path and try again."
                )

            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            return getattr(mod, pluging_class_name)(plugin_config)

        else:
            raise ValueError(
                "Compute engine configuration must include either'compute_engine_plugin_module'\
                              or 'compute_engine_plugin_path'."
            )

    def __init__(
        self,
        name: str,
        compute_engine_config: str = None,
        catalog_config: str = None,
        config_dir: Path = None,
    ):
        self.name = name
        self.data_products: dict[str, DataProduct] = {}
        self._dependencies: dict[str, tuple[str, ...]] = {}
        self.compute_engine: ComputeEnginePlugin | None = None

        if compute_engine_config:
            self.compute_engine = self.load_plugin("compute_engine", compute_engine_config, config_dir)

    def add_data_product(self, data_product: DataProduct) -> None:
        """
        Add a data product to the context instance.

        Args:
            data_product (DataProduct): The data product to add.
        """

        if self.compute_engine:
            data_product.set_compute_engine(self.compute_engine)

        self.data_products[data_product.name] = data_product
        self._dependencies[data_product.name] = tuple(data_product.inputs)

    def get_data_product(self, name: str) -> DataProduct:
        """
        Get a specific data product from the current context instance.

        Args:
            name (str): The name of the data product to retrieve.

        Returns:
            DataProduct: The requested data product instance.
        """

        if name in self.data_products:
            return self.data_products[name]
        else:
            raise ValueError(f"Data product '{name}' not found in the context instance.")

    def get_graph_sequence(self) -> list[str]:
        """
        This also checks for topological problems

        Returns:
            list[str]: A list of data product names in the order they should be executed.
        """

        try:
            graph = TopologicalSorter()
            for name, deps in self._dependencies.items():
                graph.add(name, *deps)

            return [s for s in graph.static_order() if s in self.data_products]
        except CycleError as e:
            print("❌ Cycle detected in the process dependencies!")
            print("Loop involving:", e.args[1])

    def get_dependencies(self) -> dict[str, tuple[str, ...]]:
        """
        Return a shallow copy of the dependency map (data product -> required inputs).

        Returns:
            dict[str, tuple[str, ...]]: Mapping of each data product to its declared inputs.
        """

        return dict(self._dependencies)

    def get_upstream(self, name: str) -> set[str]:
        """
        Get all the upstream dependencies for a given data product.

        Args:
            name (str): The name of the data product.

        Returns:
            set[str]: A set of upstream data product names.
        """
        if name not in self._dependencies:
            return set()

        upstream_nodes = []
        nodes_to_visit = [name]
        visited = set()

        while nodes_to_visit:
            current_node = nodes_to_visit.pop(0)
            if current_node in visited:
                continue

            visited.add(current_node)
            upstream_nodes.insert(0, current_node)

            # Assuming self._dependencies stores node -> list of parents
            parents = self._dependencies.get(current_node, [])
            nodes_to_visit.extend(parents)
        return upstream_nodes

    def get_downstream(self, name: str) -> set[str]:
        """
        Get all the downstream dependencies for a given data product.

        Args:
            name (str): The name of the data product.

        Returns:
            set[str]: A set of downstream data product names.
        """
        # First, build the reverse dependency graph (dependents graph)
        dependents = {node: [] for node in self._dependencies}
        for node, dependencies in self._dependencies.items():
            for dep in dependencies:
                if dep in dependents:
                    dependents[dep].append(node)

        # Now, traverse the dependents graph to find all downstream nodes
        downstream_nodes = []
        nodes_to_visit = [name]
        visited = set()

        while nodes_to_visit:
            current_node = nodes_to_visit.pop(0)
            if current_node in visited:
                continue

            visited.add(current_node)
            downstream_nodes.append(current_node)

            if current_node in dependents:
                nodes_to_visit.extend(dependents[current_node])

        return downstream_nodes

    def run_data_product(self, name: str):
        """
        Run a specific data product by name.

        Args:
            name (str): The name of the data product to run.

        """

        if name in self.data_products:
            print(f"⚡️ Running data product: {name}")
            self.data_products[name].run()
        else:
            print(f"Data product '{name}' is not defined")

    def run(self, name: str = None, upstream: bool = False, downstream: bool = False) -> None:
        """
        Run the process, given the initial conditions.

        Args:
            name (str): The name of the data product to start from.
            upstream (bool): If True, run all upstream data products related to the one specified.
            downstream (bool): If True, run all downstream data products related to the one specified.
        """
        if upstream:
            data_products = self.get_upstream(name)
        elif downstream:
            data_products = self.get_downstream(name)
        elif name is None:
            data_products = self.get_graph_sequence()
        else:
            g = self.get_graph_sequence()
            # get the index of the data product to continue from
            data_product_idx = g.index(name) if name in g else 0
            # just run single data product
            data_products = g[data_product_idx : data_product_idx + 1]

        # run data products
        for s in data_products:
            self.run_data_product(s)

    def visualize(self, mermaid: bool = False, textual: bool = False) -> None:
        """
        Visualize the run in different formats.

        Args:
            mermaid (bool): If True, generate a Mermaid diagram.
            textual (bool): If True, open a Textual TUI to inspect the graph.
        """

        def build_mermaid_lines(*, include_labels: bool = True, include_classdefs: bool = True) -> list[str]:
            def sanitize(name: str) -> str:
                return re.sub(r"[^0-9A-Za-z_]", "_", name)

            def node_label(name: str) -> str:
                return name.replace("_", " ").title() if include_labels else name

            lines: list[str] = ["flowchart TD"]

            defined_data_products = {name: sanitize(name) for name in self.get_graph_sequence()}
            external_nodes: dict[str, str] = {}

            if include_labels:
                for original_name, node_id in defined_data_products.items():
                    lines.append(f'    {node_id}["{node_label(original_name)}"]')

            for name in self.get_graph_sequence():
                data_product = self.data_products[name]
                for input_name in data_product.inputs:
                    if input_name in defined_data_products:
                        lines.append(
                            f"    {defined_data_products[input_name]} --> {defined_data_products[name]}"
                        )
                    else:
                        ext_id = f"ext_{sanitize(input_name)}"
                        if ext_id not in external_nodes:
                            external_nodes[ext_id] = node_label(input_name)
                            if include_labels:
                                lines.append(f'    {ext_id}["{node_label(input_name)}"]')
                        lines.append(f"    {ext_id} -.-> {defined_data_products[name]}")

            if include_labels and external_nodes and include_classdefs:
                lines.append("    classDef external fill:#f5f5f5,stroke:#999,stroke-width:1px;")
                for ext_id in external_nodes:
                    lines.append(f"    {ext_id}:::external")

            return lines

        if textual:
            from tidylake.visualization.textual_viewer import run_textual_viewer

            run_textual_viewer(self)
            return

        if mermaid:
            lines = build_mermaid_lines(include_labels=True, include_classdefs=True)
            print("```mermaid")
            for line in lines:
                print(line)
            print("```")

        else:
            for i, name in enumerate(self.get_graph_sequence(), 1):
                print(f"{i:02d}. {name}")

    def peek_data_product(self, name: str) -> None:
        """
        Peek into a specific data product by name.

        Args:
            name (str): The name of the data product to peek into.

        """

        if name in self.data_products:
            print(f"⚡️ Peeking into data product: {name}")
            self.data_products[name].peek()
        else:
            print(f"Data product '{name}' is not defined")

    def schema_diff(self, name: str = None) -> None:
        """
        Return schema differences for the selected data products.

        Args:
            name (str, optional): The name of a specific data product to check.
                If None, check all data products. Defaults to None.
        """

        if not self.compute_engine:
            print("No compute engine configured, cannot check schema.")
            return

        data_products_to_check = [self.get_data_product(name)] if name else self.data_products.values()

        return {
            data_product.name: data_product.get_schemas()
            for data_product in data_products_to_check
            if data_product.compute_engine
        }

    def schema_update(self, name: str = None, commit: bool = False) -> None:
        """
        Update or create the schema in the compute engine catalog for the selected data products.

        Args:
            name (str, optional): The name of a specific data product to update.
                If None, update all data products. Defaults to None.
            commit (bool): If True, perform the update/create operation.
                If False, only print what would be done.
        """

        if not self.compute_engine:
            print("No compute engine configured, cannot check schema.")
            return

        data_products_to_update = [self.get_data_product(name)] if name else self.data_products.values()

        for data_product in data_products_to_update:
            if data_product.compute_engine and data_product.schema:
                print(f"⚡️ Updating/Creating schema for data product: {data_product.name}")
                data_product.update_or_create_schema(commit=commit)


def get_or_create_context(config_file_path: str = None) -> TidyLakeContext:
    """
    Get the current context instance.

    Returns:
        TidyLakeContext: The current context instance.
    """
    global context

    # If the context instance is already created, return it, else create a new one
    if context is None:
        # Load the context configuration
        config_file = config_file_path if config_file_path else DEFAULT_CONFIG_FILE
        context_config = TidyLakeContext.get_config(config_file)

        # Get the directory of the context config file to resolve relative paths
        context_config_dir = Path(config_file).parent

        context_config_data = context_config.get("tidylake", {})

        context_config_data_plugins = context_config_data.get("plugins", {})

        # Initialize the context instance
        context = TidyLakeContext(
            name=context_config_data.get("name", "tidylake"),
            compute_engine_config=context_config_data_plugins.get("compute_engine"),
            config_dir=context_config_dir,
        )

        # Create and add data products from the configuration
        include_data_products = context_config_data.get("include_data_products", [])

        for data_product_config_file in include_data_products:
            # Resolve data product config file path relative to config directory
            data_product_config_path = context_config_dir / data_product_config_file

            # Load the data product configuration
            data_product_config = DataProduct.get_config(str(data_product_config_path))

            # Create a Data product instance from the configuration
            data_product = DataProduct(
                name=data_product_config.get("data_product").get("name"),
                schema=data_product_config.get("data_product").get("schema", {}),
                script=data_product_config.get("data_product").get("script", ""),
                config_dir=context_config_dir,
            )

            # Add the data product
            context.add_data_product(data_product)

    return context
