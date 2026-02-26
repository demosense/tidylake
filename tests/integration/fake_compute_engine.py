from tidylake.plugins.compute_engine import ComputeEnginePlugin


class FakeComputeEngine(ComputeEnginePlugin):
    def __init__(self, plugin_config):
        self.datasets = {}

    def read_dataset(self, name: str):
        return self.datasets.get(name)

    def write_dataset(self, name: str, df):
        self.datasets[name] = df

    def read_synthetic_dataset(self, manifest_schema: dict):
        # For simplicity, returning an empty dict.
        # This can be improved to generate synthetic data based on the schema.
        return {}

    def check_catalog_exists(self, name: str):
        return name in self.datasets

    def get_schema_from_catalog(self, name: str):
        # Not implemented for the fake engine
        return None

    def manifest_schema_to_engine_schema(self, manifest_schema: str):
        # Not implemented for the fake engine
        return None

    def engine_schema_to_manifest_schema(self, catalog_schema):
        # Not implemented for the fake engine
        return None

    def create_table(self, name: str, manifest_schema: str):
        # Not implemented for the fake engine
        pass

    def alter_table_add_column(self, table_name: str, column_name: str, column_type: str):
        # Not implemented for the fake engine
        pass

    def alter_table_drop_column(self, table_name: str, column_name: str):
        # Not implemented for the fake engine
        pass

    def alter_table_alter_column(self, table_name: str, column_name: str, column_type: str):
        # Not implemented for the fake engine
        pass
