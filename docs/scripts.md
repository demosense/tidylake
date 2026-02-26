---
title: Script Files
---

The Script File is where the actual data transformation happens. It bridges the gap between tidylake's metadata management and your chosen processing framework (pandas, Spark, Polars, etc.).

While tidylake automates the flow of metadata and enforces best practices,

## Initializing a Data Product

The only mandatory step in any script is loading the data product context. This connects the script to its corresponding  [manifest file](./manifests.md).

```python
from tidylake import get_or_create_context

data_product = get_or_create_context().get_data_product("bronze_customers")
```

## The Data Product Lifecycle

A typical script manages the following lifecycle stages:

The main body of script will be dedicated to managing the data product lifecycle, which can contain some the following steps:

- **Reading Inputs:** Loading dependency datasets.
- **Transformation:** Implementing the business logic.
- **Validation:** Running data quality and schema checks.
- **Writing Outputs:** Persisting the result to storage via Sinks.

### Reading data {#reading-data}

Reading data through tidylake provides several benefits:

- **Implicit Lineage:** Automatically builds your [dependency DAG](context.md#dag).
- **Environment Agnosticism:** Reproduce code across local and cloud environments via [compute engine plugin](plugins/compute-engine.md).
- **Simplified Testing:** Automatically swap real data for synthetic data during development.

#### Option A: Explicit Input

Use this for specific data origins or smaller projects without a compute plugin.

```python
@data_product.add_input() # (1)!
def bronze_customers(): # (2)!
    return pd.read_parquet("s3://my-bucket/bronze_customers")

df_bronze_profile = bronze_profile()
```

1. This decorator registers the function as a dependency, handling the metadata link transparently.
2. We recommend setting the name of the data product as the name of the function, the library will look for a manifest file with the same name. You can also set the name manually (see [data product API definition]('api/data-product.md#tidylake.DataProduct.add_input'))

#### Option B: Plugin-managed Input (Recommended)

If you use a [compute engine plugin](plugins/compute-engine.md), your code becomes much leaner. This simpler one liner will handle everything mentioned under the hood:

```python
df_bronze_customers = data_product.read_input("bronze_customers")
```

This one liner will handle everything mentioned under the hood.

#### Extra: External/Raw Data

For data not managed by a tidylake manifest (e.g., raw logs), use the `raw=True` flag. This option will not look for a manifest file inside your project:

```python
@data_product.add_input(raw=True)
def raw_customers():
    return pd.read_parquet("s3://my-bucket/raw-customers.json")

df_raw_customers = raw_customers()
```

### Logging Data Quality {#data-quality}

> WIP

### Writing Data (Sinks) {#writing-data}

In tidylake, writing data is handled through a **sink**. Unlike a standard function call that executes immediately, a sink allows you to define how data should be serialized while deferring the execution to the framework's controller.

This abstraction handles several critical tasks under the hood:

- **Execution Safety:** It prevents "side effects" (writing data) during development. Sinks are automatically disabled when running in [interactive mode](#script-vs-interactive) or during unit tests, providing a safe playground where you can run your script repeatedly without polluting production storage.
- **Engine Encapsulation:** Like the reading helpers, Sinks can be managed by a [compute engine plugin](plugins/compute-engine.md). This ensures that your serialization logic (paths, credentials, and formats) is reproducible across different environments (e.g., local Parquet vs. S3 Delta Lake).

### Option A: Defining a Data Sink Directly

By wrapping your serialization code in the `@data_product.set_sink()` decorator, you are telling tidylake: *"This is how I want to save my data, but only execute this when I explicitly run the pipeline."*

In a data product script, serialization will only occur when the script is invoked via the run command in the CLI or the SDK.

```python
df_bronze_customers = ... # (1)!

@data_product.set_sink() # (2)!
def write_bronze_customers():
    return df_bronze_customers.to_parquet("/tmp/bronze_customers", index=False)
```

1. **Agnostic Logic:** You can reference any variable (like a DataFrame) defined earlier in your script. This keeps your core transformation logic completely independent of the storage implementation.
2. **Deferred Execution:** This decorator ensures the function is registered but not executed during standard script imports or interactive kernel runs.

### Option B: Plugin-managed Sink

To maximize the framework's power, we recommend using the compute plugin to manage sinks. This removes hardcoded paths and formats from your scripts entirely.

By using this one-liner, you ensure that the same script can write to a local directory for a developer and a governed production table for the DataOps team, all controlled by the framework's configuration.

```python
data_product.set_output_data(df_silver_customers)
```

## Script vs. Interactive Mode {#script-vs-interactive}

Tidylake is designed to solve the [the Notebook vs. Script Dilemma](design-principles.md#batch-vs-interactive). By using our helpers and following this methodology, you gain a seamless experience where the same file serves two masters: the analyst's curiosity and the engineer's rigour.

#### How it works

Internally, the package detects whether you are running the code as a standalone script (via the CLI `run` command or the SDK) or within a REPL/Interactive kernel (such as a Jupyter Notebook or an IPython session).

Tidylake prioritizes developer experience. It provides helpers to automatically display data previews, enables [synthetic data generation](plugins/compute-engine.md#synthetic-data) for rapid prototyping, and—most importantly—disables sinks to prevent accidental writes.

We recommend developing your pipelines interactively to iterate quickly, then promoting that exact same code base to production. This "One Code Base" approach eliminates the errors typically introduced when "translating" a notebook into a production script.

### Reference Examples

While you can use standard .ipynb notebooks, we often use [vscode jupyter code cells](https://code.visualstudio.com/docs/python/jupyter-support-py#_jupyter-code-cells) (# %%) in our [demos](demos/demos.md). This format allows the file to remain a plain Python script while offering a notebook-like interface.

#### Example I: Compute plugin managed

```python {with_compute_engine.py}
# %%
from tidylake import get_or_create_context

data_product = get_or_create_context().get_data_product("silver_customers")

# %%
df_bronze_customers = data_product.read_input("bronze_customers")

# %%
df_silver_customers = df_bronze_customers.rename(
    columns={
        "customer__id": "customer_id",
        "customer__name": "customer_name",
        "customer__active": "customer_active",
        "customer__city": "customer_city",
    }
)

# %%
data_product.set_output_data(df_silver_customers)
```

!!!info "Complete example"
    See complete example in context in the [pandas pyiceberg demo](demos/pandas-pyiceberg.md).


#### Example II: No compute plugin

```python {without_compute_engine.py}
# %%
import pandas as pd

from tidylake import get_or_create_context

data_product = get_or_create_context().get_data_product("silver_customers")

# %%
@data_product.add_input()
def bronze_customers():
    return pd.read_parquet("/tmp/bronze_customers")


df_bronze_customers = bronze_customers()

# %%
@data_product.add_input()
def bronze_profile():
    return pd.read_parquet("/tmp/bronze_profile")

df_bronze_profile = bronze_profile()

# %%
df_silver_customers = (
    df_bronze_customers.loc[lambda df: df["customer__active"]]
    .merge(df_bronze_profile, left_on="customer__id", right_on="profile__id", how="left")
    .rename(
        columns={
            "customer__id": "customer_id",
            "customer__name": "customer_name",
            "customer__city": "customer_city",
            "profile__account": "customer_account",
        }
    )
    .assign(
        customer_city=lambda df: df["customer_city"].str.upper(),
        customer_name=lambda df: df["customer_name"].str.title(),
    )
    .sort_values(by="customer_id")[["customer_id", "customer_name", "customer_city", "customer_account"]]
)

# %%
@data_product.set_sink()
def write_silver_customers():
    return df_silver_customers.to_parquet("/tmp/silver_customers", index=False)
```

!!!info "Complete example"
    See complete example in context in the [pandas local demo](demos/pandas-local.md).