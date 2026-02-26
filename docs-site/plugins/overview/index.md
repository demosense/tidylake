By design, tidylake only provides the core "orchestration of metadata" through [context](https://github.com/demosense/tidylake/context/index.md), [manifest](https://github.com/demosense/tidylake/manifests/index.md), and [script](https://github.com/demosense/tidylake/scripts/index.md) files. Our objective is to provide a methodology for managing complex data platforms without becoming a bottleneck for your technology choices.

We intentionally leave infrastructure-specific functionality to the user. It is impossible to provide a "one-size-fits-all" solution for every combination of Spark, Snowflake, S3, or BigQuery. Instead, we provide the ports, and you (or our community) provide the adapters.

## Architecture: Ports and Adapters

This design follows the **Hexagonal Architecture** (or Ports and Adapters) pattern. In this model:

- **The Core:** Your data product definitions and transformation logic remain agnostic of the underlying infrastructure.
- **The Ports:** Tidylake defines "ports"—interfaces for common tasks like reading data, writing data, or updating a catalog.
- **The Adapters (Plugins):** These are the specific implementations that connect your core to the outside world (e.g., a "Spark-S3 Adapter" or a "DuckDB-Local Adapter").

This approach respects the **Open-Closed Principle**: tidylake is open for extension (you can add any technology via plugins) but closed for modification (you never have to change the core tidylake engine to support a new database).

## Currently Supported Plugins

### Compute Engine

The [compute engine plugin](https://github.com/demosense/tidylake/plugins/compute-engine/index.md) manages the end-to-end lifecycle of data serialization and storage. It handles:

- **I/O Operations:** Abstracting the complexity of reading/writing from object storage (S3/Azure/GCS) or OLAP databases.
- **Catalog Automation:** Automatically managing schema definitions in metastores (Hive, AWS Glue) for formats like Parquet, Delta Lake, or Apache Iceberg.
- **Synthetic Data:** Providing framework-specific adapters to generate test data directly into your dataframes for prototyping.

### Data Quality Tracker (WIP)

A non-opinionated tracker designed to manage logs, alerts, and statistics generated during data profiling and validation. This plugin acts as the bridge between your execution pipeline and your governance/observability platforms.

## How the Plugin System Works

Tidylake defines plugins as abstract classes. To use them, you—or a community-provided package—simply implement the required methods. These implementations can reside in external dependencies, or directly within your project as `.py` files or local modules.

To activate a plugin, reference it in your [context file](https://github.com/demosense/tidylake/context/index.md). Tidylake will dynamically load the module and inject it into your data product lifecycle.

Because the context file is flexible, you can also include arbitrary properties required by your specific implementation (such as API keys, environment flags, or storage paths).
