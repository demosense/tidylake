from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

from tidylake.plugins.compute_engine import ComputeEnginePlugin

# map Spark types → JSON Schema types
JSONSCHEMA_SPARK_MAPPING = {
    "string": "string",
    "integer": "integer",
    "long": "integer",
    "double": "number",
    "float": "number",
    "boolean": "boolean",
    "timestamp": "string",
    "date": "string",
}

# map JSON Schema types → Spark types
SPARK_JSONSCHEMA_MAPPING = {
    "string": "string",
    "integer": "integer",
    "number": "double",
    "boolean": "boolean",
    # TODO: jsonschema has less types than spark and other frameworks....
    "timestamp": "string",
    "date": "string",
}


class SparkComputeEnginePlugin(ComputeEnginePlugin):
    def __init__(self, compute_engine_config: dict = None):
        super().__init__()

        # Retrieve config
        if compute_engine_config is None:
            compute_engine_config = {}

        app_name = compute_engine_config.get("spark_app_name", "TIDYLAKE")
        spark_connect_host = compute_engine_config.get("spark_connect_host", "localhost")
        spark_connect_port = compute_engine_config.get("spark_connect_port", 15002)
        spark_sql_warehouse_dir = compute_engine_config.get("spark_sql_warehouse_dir", "warehouse")

        self.spark = (
            SparkSession.builder.appName(app_name)
            .remote(f"sc://{spark_connect_host}:{spark_connect_port}")
            .config("spark.sql.warehouse.dir", spark_sql_warehouse_dir)
            .getOrCreate()
        )

    def read_dataset(self, name: str) -> DataFrame:
        return self.spark.table(name)

    def read_synthetic_dataset(self, manifest_schema: dict):
        raise NotImplementedError("Synthetic data generation not implemented for SparkComputeEnginePlugin.")

    def write_dataset(
        self,
        name: str,
        df: DataFrame,
    ):
        if not self.check_catalog_exists(name):
            print("ERROR: Table does not exist in catalog. Create schema first.")
            return

        # (df.write.option("path", f"/tmp/{name}").mode("overwrite").saveAsTable(name))
        df.write.insertInto(name, overwrite=True)

    def check_catalog_exists(self, name: str):
        return self.spark.catalog.tableExists(name)

    def get_schema_from_catalog(self, name: str) -> dict:
        if self.check_catalog_exists(name):
            spark_schema = self.spark.table(name).schema.jsonValue()
            json_schema = self.engine_schema_to_manifest_schema(spark_schema)

            return json_schema

    def manifest_schema_to_engine_schema(self, manifest_schema: str):
        def convert_field(name, props):
            json_type = props.get("type")

            if json_type == "object":
                return {
                    "type": "struct",
                    "fields": [
                        {"name": name, "type": convert_field(v), "nullable": True}
                        for k, v in props.get("properties", {}).items()
                    ],
                }

            return {
                "name": name,
                "type": SPARK_JSONSCHEMA_MAPPING.get(json_type, "string"),
                "nullable": True,
            }

        return {
            "fields": [convert_field(name, props) for name, props in manifest_schema["properties"].items()],
        }

    def engine_schema_to_manifest_schema(self, catalog_schema):
        def convert_field(field):
            spark_type = field.get("type")

            if spark_type == "struct":
                return {
                    "type": "object",
                    "properties": {f["name"]: convert_field(f) for f in spark_type["fields"]},
                }

            return {"type": JSONSCHEMA_SPARK_MAPPING.get(spark_type, "string")}

        return {
            "type": "object",
            "properties": {f["name"]: convert_field(f) for f in catalog_schema["fields"]},
        }

    def validate_dataset_schema(self, manifest_schema, df):
        # TODO: implement more robust schema validation (e.g. check types, handle nested schemas, etc.)
        manifest_columns = set(manifest_schema.get("properties", {}).keys())
        df_columns = set(df.columns)

        return manifest_columns.issubset(df_columns)

    def create_table(self, name: str, manifest_schema: str):
        spark_schema = self.manifest_schema_to_engine_schema(manifest_schema)
        schema = StructType.fromJson(spark_schema)
        self.spark.catalog.createTable(tableName=name, schema=schema, source="delta")

        self.spark.sql(f"ALTER TABLE {name} SET TBLPROPERTIES ('delta.columnMapping.mode' = 'name')")

    def alter_table_add_column(self, table_name: str, column_name: str, column_type: str):
        self.spark.sql(
            f"ALTER TABLE {table_name} ADD COLUMNS ({column_name} {JSONSCHEMA_SPARK_MAPPING[column_type]})"
        )

    def alter_table_drop_column(self, table_name: str, column_name: str):
        self.spark.sql(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")

    def alter_table_alter_column(self, table_name: str, column_name: str, column_type: str):
        self.spark.sql(
            f"ALTER TABLE {table_name} CHANGE COLUMN {column_name} {column_name}\
                  {JSONSCHEMA_SPARK_MAPPING[column_type]}"
        )
