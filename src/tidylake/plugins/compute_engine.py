from abc import ABC, abstractmethod

from tidylake.core.commons import (
    EXECUTION_MODE_INTERACTIVE,
    execution_mode,
    get_use_synthetic_data_sample_size,
)


class ComputeEnginePlugin(ABC):
    @abstractmethod
    def read_dataset(self, name: str):
        """
        Read dataset from the compute engine catalog.
        The implementation should return a dataframe in the native format of the
        compute engine (e.g. Spark DataFrame, Pandas DataFrame, etc.).

        Args:
            name (str): The name of the data product in the project.

        Returns:
            DataFrame: The dataset as a dataframe in the native format of the compute engine.
        """
        pass

    def display_dataset(self, df):
        """
        Display dataset in the appropriate format based on the execution environment.

        If the execution mode is interactive (e.g. Jupyter notebook), use rich display.
        Otherwise, print the dataframe in a simple format. Method can be overridden
        by compute engine plugins to provide custom display logic.

        Args:
            df: The dataset as a dataframe in the native format of the compute engine.
        """
        if execution_mode == EXECUTION_MODE_INTERACTIVE:
            display(df)  # type: ignore  # noqa: F821
        else:
            # TODO: update to rich table display
            print(df)

    @abstractmethod
    def read_synthetic_dataset(self, manifest_schema: dict):
        """
        Generate synthetic dataset based on the manifest schema and return it as a dataframe
        in the native format of the compute engine.
        The implementation should return a dataframe in the native format of the compute engine
        (e.g. Spark DataFrame, Pandas DataFrame, etc.).

        Args:
            manifest_schema (dict): The schema defined in the manifest file.
        Returns:
            DataFrame: The synthetic dataset as a dataframe in the native format of the compute engine.
        """
        pass

    @abstractmethod
    def write_dataset(self, name: str, df):
        """
        Write dataset to the compute engine catalog.
        The implementation should handle writing the dataframe to the compute
        engine catalog in the appropriate format.

        Args:
            name (str): The name of the data product in the project.
            df: The dataset as a dataframe in the native format of the compute engine.
        """
        pass

    @abstractmethod
    def check_catalog_exists(self, name: str):
        """
        Check if dataset exists in the compute engine catalog.
        The implementation should check if the dataset with the given name exists
        in the compute engine catalog.

        Args:
            name (str): The name of the data product in the project.
        Returns:
            bool: True if the dataset exists in the compute engine catalog, False otherwise.
        """
        pass

    @abstractmethod
    def get_schema_from_catalog(self, name: str):
        """
        Get the schema of the dataset from the compute engine catalog.
        The implementation should retrieve the schema of the dataset with the given name
        from the compute engine catalog.

        Args:
            name (str): The name of the data product in the project.
        Returns:
            dict: The schema of the dataset.
        """
        pass

    @abstractmethod
    def manifest_schema_to_engine_schema(self, manifest_schema: str):
        """
        Convert a manifest schema to the compute engine's native schema format.

        Args:
            manifest_schema (str): The schema defined in the manifest file.
        Returns:
            dict: The schema in the compute engine's native format.
        """
        pass

    @abstractmethod
    def engine_schema_to_manifest_schema(self, catalog_schema: dict):
        """
        Convert a compute engine's native schema to a manifest schema.

        Args:
            catalog_schema (dict): The schema in the compute engine's native format.
        Returns:
            dict: The schema in the manifest format.
        """
        pass

    @abstractmethod
    def validate_dataset_schema(self, manifest_schema: dict, df) -> bool:
        """
        Optional function to validate the manifest schema against a dataset
        during the execution of the data product script.

        Args:
            manifest_schema (dict): The schema defined in the manifest file.
            df: The dataset as a dataframe in the native format of the compute engine.
        Returns:
            bool: True if the dataset matches the manifest schema, False otherwise.
        """
        pass

    @abstractmethod
    def create_table(self, name: str, manifest_schema: str):
        """
        Create a new table in the compute engine catalog.

        Args:
            name (str): The name of the data product in the project.
            manifest_schema (str): The schema defined in the manifest file.
        """
        pass

    @abstractmethod
    def alter_table_add_column(self, table_name: str, column_name: str, column_type: str):
        """
        Add a new column to an existing table in the compute engine catalog.

        Args:
            table_name (str): The name of the table in the catalog.
            column_name (str): The name of the column to add.
            column_type (str): The type of the column to add.
        """
        pass

    @abstractmethod
    def alter_table_drop_column(self, table_name: str, column_name: str):
        """
        Drop a column from an existing table in the compute engine catalog.
        Args:
            table_name (str): The name of the table in the catalog.
            column_name (str): The name of the column to drop.
        """
        pass

    @abstractmethod
    def alter_table_alter_column(self, table_name: str, column_name: str, column_type: str):
        """
        Alter the type of a column in an existing table in the compute engine catalog.
        Args:
            table_name (str): The name of the table in the catalog.
            column_name (str): The name of the column to alter.
            column_type (str): The new type of the column.
        """
        pass

    @staticmethod
    def compute_changeset(manifest_schema: dict, catalog_schema: dict):
        manifest_props = manifest_schema.get("properties", {}) if manifest_schema else {}
        catalog_props = catalog_schema.get("properties", {}) if catalog_schema else {}

        manifest_keys = set(manifest_props.keys())
        catalog_keys = set(catalog_props.keys())

        changeset = []
        for key in manifest_keys | catalog_keys:
            if key not in catalog_keys:
                # Column exists only in defined schema → ADD
                manifest_type = manifest_props[key].get("type")
                changeset.append(("ADD", key, manifest_type))
            elif key not in manifest_keys:
                # Column exists only in catalog schema → DROP
                changeset.append(("DROP", key, None))
            else:
                manifest_type = manifest_props[key].get("type")
                cat_type = catalog_props[key].get("type")
                if manifest_type != cat_type:
                    # Type mismatch → ALTER (use Spark type for SQL statement)
                    changeset.append(
                        (
                            "ALTER",
                            key,
                            manifest_type,
                        )
                    )
        return changeset

    def update_or_create_schema(self, name: str, manifest_schema: str, commit: bool = False):
        # Check if table exists in catalog
        if not self.check_catalog_exists(name):
            print(f"Table {name} does not exist. A new table will be created.")

            if not commit:
                print("Dry run mode, not creating table.")
                return

            self.create_table(name, manifest_schema)

        # Table exists, check for schema changes
        else:
            # Compute schema changes reusing the same diff strategy used by the CLI
            catalog_schema = self.get_schema_from_catalog(name)

            changeset = self.compute_changeset(manifest_schema, catalog_schema)

            print(f"Schema changes for table {name}:")
            for change in changeset:
                print(f"{change[0]:6} {change[1]:20} {change[2]}")

            if not commit:
                print("Dry run mode, not applying changes.")
                return

            # Apply schema changes to the table in the catalog
            for op, col_name, col_type in changeset:
                if op == "ADD":
                    self.alter_table_add_column(name, col_name, col_type)
                elif op == "DROP":
                    self.alter_table_drop_column(name, col_name)
                elif op == "ALTER":
                    self.alter_table_alter_column(name, col_name, col_type)

    def generate_synthetic_data_from_manifest(self, manifest_schema: dict) -> dict:
        synthetic_data = {}

        for prop_name, prop_definition in manifest_schema.get("properties", {}).items():
            jtype = prop_definition.get("type", "string")

            n = get_use_synthetic_data_sample_size()

            if jtype == "string":
                data = [f"sample_{prop_name}" for _ in range(n)]
            elif jtype == "integer":
                data = [123 for _ in range(n)]
            elif jtype == "number":
                data = [123.45 for _ in range(n)]
            elif jtype == "boolean":
                data = [True for _ in range(n)]
            else:
                data = [None for _ in range(n)]

            synthetic_data[prop_name] = data

        return synthetic_data
