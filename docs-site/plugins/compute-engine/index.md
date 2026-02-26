The **Compute Engine Plugin** is the primary driver of automation in the tidylake ecosystem. It bridges the gap between your metadata definitions and your actual storage and compute infrastructure.

While the core library handles the "logic" of your DAG, this plugin handles the "physics" of reading, writing, and maintaining your data lakehouse.

## Plugin Configuration

### Adapter Implementation

To use this plugin, you must implement the [ComputeEnginePlugin](https://github.com/demosense/tidylake/api/compute-engine-plugin/index.md) abstract class. This adapter serves as the translator between tidylake and your specific stack (e.g., Spark, Snowflake, or Pandas + Iceberg).

### Context Configuration

Register your implementation in the [context file](https://github.com/demosense/tidylake/context/index.md) so the framework can discover it at runtime:

```
tidylake:
    ...
    plugins: # (1)!
        type: object
        description: Plugin Configuration
        properties:
            compute_engine: # (2)!
                type: object
                description: Configuration for the compute engine plugin
                properties:
                    plugin_path: # (3)!
                        type: string
                        description: Path to the python file that defines the plugin. Takes precedence
                    plugin_module: # (4)!
                        type: string
                        description: Path to the python module that contains the plugin
                    plugin_class_name: # (5)!
                        type: string
                        description: Name of the python path inside file or module
                    # (6)!
```

1. Add a `plugins` section
1. Create the `compute_engine` property
1. Set either `plugin_path` or `plugin_module`
1. Set either `plugin_path` or `plugin_module`
1. Set your `plugin_class_name`
1. You can define additional custom properties for your custom implementation

See Real-World Implementations

Check the [pandas pyceberg demo](https://github.com/demosense/tidylake/demos/pandas-pyiceberg/index.md) or the [pyspark demo](https://github.com/demosense/tidylake/demos/pyspark/index.md) for complete, production-ready adapter code.

## Initialization

Your adapter must implement an `__init__` function. This is where you set up global state, such as attaching to an existing Spark session, authenticating with cloud providers (AWS/Azure/GCP), or initializing local catalog connections.

```
class PandasIcebergComputeEnginePlugin(ComputeEnginePlugin):
    def __init__(self, compute_engine_config: dict = None):
        super().__init__()

        warehouse_path = compute_engine_config.get("warehouse_path") # (1)!
        self.namespace = compute_engine_config.get("namespace", "default")

        os.makedirs(warehouse_path, exist_ok=True) # (2)!
        self.catalog = load_catalog(
            "default",
            **{
                "type": "sql",
                "uri": f"sqlite:///{warehouse_path}/pyiceberg_catalog.db",
                "warehouse": f"file://{warehouse_path}",
            },
        )

        self.catalog.create_namespace_if_not_exists(self.namespace)
```

1. Load config values from the context file
1. Init required sessions or temporary files for the process

Complete Example

This is an excerpt from [pandas pyceberg demo](https://github.com/demosense/tidylake/demos/pandas-pyiceberg/index.md).

## Data Serialization & Deserialization

The adapter's primary job is to handle how data products are retrieved and persisted. You must implement the [`read_dataset`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.read_dataset) and [`write_dataset`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.write_dataset) methods.

- **Reading:** Logic to load a table from a metastore (like Hive or Glue), query a warehouse (BigQuery, Snowflake) or read a plain file from an object store (S3, ADLS, GCS).
- **Writing:** Logic to serialize data to a specific format (Parquet, Delta, Iceberg) and update the corresponding catalog table via your framework serialization API or SQL statements.

```
def read_dataset(self, name: str):
    return self.catalog.load_table(f"{self.namespace}.{name}").scan().to_pandas() # (1)!

def write_dataset(self, name: str, df):
    table = self.catalog.load_table(f"{self.namespace}.{name}")
    df_arrow = pa.Table.from_pandas(df)
    table.overwrite(df_arrow)
```

1. Reuse existing sessions from the initialization

Complete Example

This is an excerpt from [pandas pyceberg demo](https://github.com/demosense/tidylake/demos/pandas-pyiceberg/index.md).

## Other Methods

Check the plugin implementation for other optional methods that can be added to the adapter such as the [`display_dataset`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.display_dataset) that will improve how the dataset is visualized during interactive mode or with the `peek` cli command.

## Schema Automation

Tidylake promotes a methodology that separates the lifecycle of data from the lifecycle of schemas. We recommend defining your "Data Contract" (the schema) in the manifest first. This enables several "Shift-Left" data engineering practices:

- **Schema Enforcement:** Prevent pipeline bugs by enforcing strict typing on write.
- **Safe Development:** Use [synthetic data](#synthetic-data) generation in early development or when real-world data access is restricted.
- **Evolution Management:** Use the CLI to track and apply changes to your catalog tables.

### Schema translation

To automate your catalog, the adapter must know how to translate tidylake [manifest types](https://github.com/demosense/tidylake/manifests/#defining-the-schema) (based on JSON Schema) into your engine's native types (e.g., PyArrow or Spark Types).

You must implement:

- [`get_schema_from_catalog`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.get_schema_from_catalog): Retrieve the current native schema as a dictionary.
- [`manifest_schema_to_engine_schema`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.manifest_schema_to_engine_schema): Convert a manifest definition into your catalog’s API format.
- [`engine_schema_to_manifest_schema`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.engine_schema_to_manifest_schema): Convert a physical catalog schema back into tidylake’s manifest format.

```
def get_schema_from_catalog(self, name: str):
    table = self.catalog.load_table(f"{self.namespace}.{name}") # (1)!
    arrow_schema = table.schema()

    return self.engine_schema_to_manifest_schema(arrow_schema)

def manifest_schema_to_engine_schema(self, manifest_schema: str):
    fields = []
    for name, prop in manifest_schema.get("properties", {}).items():
        jtype = prop.get("type", "string")
        pa_type = JSONSCHEMA_PYARROW_MAPPING.get(jtype, pa.string()) # (2)!
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
```

1. Just uses the native API
1. This is just a dict mapping. Check it out in the full example.

Complete Example

This is an excerpt from [pandas pyceberg demo](https://github.com/demosense/tidylake/demos/pandas-pyiceberg/index.md).

### Schema Manipulation

Once translation is handled, you implement the methods that actually touch the infrastructure: [`check_catalog_exists`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.check_catalog_exists), [`create_table`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.create_table), and the *alter table* suite ([`alter_table_add_column`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.alter_table_add_column), [`alter_table_drop_column`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.alter_table_drop_column), or [`alter_table_alter_column`](https://github.com/demosense/tidylake/api/compute-engine-plugin/#tidylake.plugins.compute_engine.ComputeEnginePlugin.alter_table_alter_column)).

```
def check_catalog_exists(self, name: str):
    return self.catalog.table_exists(f"{self.namespace}.{name}")


def create_table(self, name: str, manifest_schema: str):
    catalog_schema = self.manifest_schema_to_engine_schema(manifest_schema)

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
```

### Managing the Schema Lifecycle via CLI

With your adapter in place, you can use the CLI to maintain your data lakehouse without writing manual statements.

#### Step 1: Detect Discrepancies

Running [`tidylake schema diff`](https://github.com/demosense/tidylake/cli/#schema-diff) compares your manifest files against the actual physical tables in your catalog.

Run it by yourself by following the example

These commands are being run over the [pandas pyiceberg demo](https://github.com/demosense/tidylake/demos/pandas-pyiceberg/index.md).

```
$ tidylake schema diff

                       bronze_customers
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ column           ┃ defined_schema ┃ catalog_schema ┃ status ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ customer__city   │ string         │ <missing>      │ ADD    │
│ customer__active │ boolean        │ <missing>      │ ADD    │
│ customer__id     │ string         │ <missing>      │ ADD    │
│ customer__name   │ string         │ <missing>      │ ADD    │
└──────────────────┴────────────────┴────────────────┴────────┘
                       silver_customers
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ column          ┃ defined_schema ┃ catalog_schema ┃ status ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ customer_active │ boolean        │ <missing>      │ ADD    │
│ customer_city   │ string         │ <missing>      │ ADD    │
│ customer_name   │ string         │ <missing>      │ ADD    │
│ customer_id     │ string         │ <missing>      │ ADD    │
└─────────────────┴────────────────┴────────────────┴────────┘
```

### Step 2: Apply Changes

Use the [`tidylake schema update`](https://github.com/demosense/tidylake/cli/#schema-update) command to align the catalog with your manifests. We recommend a "Dry Run" first, followed by a `--commit` once you have verified the changes.

```
$ tidylake schema update --data-product bronze_customers
⚡️ Updating/Creating schema for data product: bronze_customers
Table bronze_customers does not exist. A new table will be created.
Dry run mode, not creating table.
```

```
$ tidylake schema update --data-product bronze_customers --commit
⚡️ Updating/Creating schema for data product: bronze_customers
Table bronze_customers does not exist. A new table will be created.
```

Now that the table has been created, we can run `tidylake schema diff` again to sverifyee the changes in our catalog:

```
$ tidylake schema diff
                       bronze_customers
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ column           ┃ defined_schema ┃ catalog_schema ┃ status ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ customer__id     │ string         │ string         │ OK     │
│ customer__active │ boolean        │ boolean        │ OK     │
│ customer__city   │ string         │ string         │ OK     │
│ customer__name   │ string         │ string         │ OK     │
└──────────────────┴────────────────┴────────────────┴────────┘
                       silver_customers
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ column          ┃ defined_schema ┃ catalog_schema ┃ status ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ customer_active │ boolean        │ <missing>      │ ADD    │
│ customer_city   │ string         │ <missing>      │ ADD    │
│ customer_name   │ string         │ <missing>      │ ADD    │
│ customer_id     │ string         │ <missing>      │ ADD    │
└─────────────────┴────────────────┴────────────────┴────────┘
```

If you later modify a manifest file, running `tidylake schema diff` will detect the drift; running `tidylake schema update --commit` will apply the necessary commands automatically.

```
$ tidylake schema diff --data-product bronze_customers
                       bronze_customers
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ column           ┃ defined_schema ┃ catalog_schema ┃ status ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ customer__active │ boolean        │ boolean        │ OK     │
│ customer__city   │ <missing>      │ string         │ DROP   │
│ customer__email  │ string         │ <missing>      │ ADD    │
│ customer__id     │ string         │ string         │ OK     │
│ customer__name   │ string         │ string         │ OK     │
└──────────────────┴────────────────┴────────────────┴────────┘
```

```
$ tidylake schema update --data-product bronze_customers --commit
⚡️ Updating/Creating schema for data product: bronze_customers
Schema changes for table bronze_customers:
ADD    customer__email      string
DROP   customer__city       None
```

```
$ tidylake schema diff --data-product bronze_customers
                       bronze_customers
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ column           ┃ defined_schema ┃ catalog_schema ┃ status ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ customer__email  │ string         │ string         │ OK     │
│ customer__active │ boolean        │ boolean        │ OK     │
│ customer__id     │ string         │ string         │ OK     │
│ customer__name   │ string         │ string         │ OK     │
└──────────────────┴────────────────┴────────────────┴────────┘
```

Now you are ready to run the script files and start working with your data.

## Working with synthetic data

> WIP
