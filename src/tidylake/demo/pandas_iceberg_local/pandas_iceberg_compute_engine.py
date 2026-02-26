import os

import pandas as pd
import pyarrow as pa
from pyiceberg.catalog import load_catalog
from pyiceberg.types import (
    BooleanType,
    FloatType,
    IntegerType,
    StringType,
)

from tidylake.plugins.compute_engine import ComputeEnginePlugin

JSONSCHEMA_PYARROW_MAPPING = {
    "string": pa.string(),
    "integer": pa.int64(),
    "number": pa.float64(),
    "boolean": pa.bool_(),
}

PYARROW_JSONSCHEMA_MAPPING = {
    "string": "string",
    "integer": "integer",
    "number": "number",
    "boolean": "boolean",
}

JSONSCHEMA_PYICEBERG_MAPPING = {
    "string": StringType(),
    "integer": IntegerType(),
    "number": FloatType(),
    "boolean": BooleanType(),
}


class PandasIcebergComputeEnginePlugin(ComputeEnginePlugin):
    def __init__(self, compute_engine_config: dict = None):
        super().__init__()

        warehouse_path = compute_engine_config.get("warehouse_path")
        self.namespace = compute_engine_config.get("namespace", "default")
        os.makedirs(warehouse_path, exist_ok=True)
        self.catalog = load_catalog(
            "default",
            **{
                "type": "sql",
                "uri": f"sqlite:///{warehouse_path}/pyiceberg_catalog.db",
                "warehouse": f"file://{warehouse_path}",
            },
        )

        self.catalog.create_namespace_if_not_exists(self.namespace)

    def read_dataset(self, name: str):
        return self.catalog.load_table(f"{self.namespace}.{name}").scan().to_pandas()

    def read_synthetic_dataset(self, manifest_schema: dict):
        synth_data = self.generate_synthetic_data_from_manifest(manifest_schema)

        return pd.DataFrame.from_dict(synth_data)

    def write_dataset(self, name: str, df):
        if not self.check_catalog_exists(name):
            print("ERROR: Table does not exist in catalog. Create schema first.")
            return

        table = self.catalog.load_table(f"{self.namespace}.{name}")
        df_arrow = pa.Table.from_pandas(df)
        table.overwrite(df_arrow)

    def check_catalog_exists(self, name: str):
        return self.catalog.table_exists(f"{self.namespace}.{name}")

    def display_dataset(self, df) -> None:
        # TODO: Update to rich markdown
        super().display_dataset(df.head())

    def get_schema_from_catalog(self, name: str):
        table = self.catalog.load_table(f"{self.namespace}.{name}")
        arrow_schema = table.schema()

        return self.engine_schema_to_manifest_schema(arrow_schema)

    def manifest_schema_to_engine_schema(self, manifest_schema: str):
        fields = []
        for name, prop in manifest_schema.get("properties", {}).items():
            jtype = prop.get("type", "string")
            pa_type = JSONSCHEMA_PYARROW_MAPPING.get(jtype, pa.string())
            # nullable = True if not required
            nullable = name not in manifest_schema.get("required", [])
            fields.append(pa.field(name, pa_type, nullable=nullable))

        return pa.schema(fields)

    def engine_schema_to_manifest_schema(self, catalog_schema: pa.Schema):
        return {
            "type": "object",
            "properties": {
                field.name: {"type": PYARROW_JSONSCHEMA_MAPPING.get(str(field.field_type), "string")}
                for field in catalog_schema.columns
            },
        }

    def validate_dataset_schema(self, manifest_schema, df):
        # TODO: implement more robust schema validation (e.g. check types, handle nested schemas, etc.)
        manifest_columns = set(manifest_schema.get("properties", {}).keys())
        df_columns = set(df.columns)

        return manifest_columns.issubset(df_columns)

    def create_table(self, name: str, manifest_schema: str):
        catalog_Schema = self.manifest_schema_to_engine_schema(manifest_schema)

        self.catalog.create_table(
            f"{self.namespace}.{name}",
            schema=catalog_Schema,
        )

    def alter_table_add_column(self, table_name: str, column_name: str, column_type: str):
        table = self.catalog.load_table(f"{self.namespace}.{table_name}")
        with table.update_schema() as update:
            update.add_column(
                column_name,
                JSONSCHEMA_PYICEBERG_MAPPING.get(column_type, StringType()),
            )

    def alter_table_drop_column(self, table_name: str, column_name: str):
        table = self.catalog.load_table(f"{self.namespace}.{table_name}")
        with table.update_schema() as update:
            update.delete_column(column_name)

    def alter_table_alter_column(self, table_name: str, column_name: str, column_type: str):
        table = self.catalog.load_table(f"{self.namespace}.{table_name}")
        with table.update_schema() as update:
            update.update_column(
                column_name,
                JSONSCHEMA_PYICEBERG_MAPPING.get(column_type, StringType()),
            )
