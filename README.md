<p align="center"><h1 align="center">tidylake</h1></p>

<p align="center">
    <img src="https://img.shields.io/badge/Python-3776AB.svg?style=default&logo=Python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/uv-blue?style=default&logo=python&logoColor=white" alt="uv">
    <img src="https://img.shields.io/badge/Ruff-D37D44?style=default&logo=ruff&logoColor=white" alt="Ruff">
    <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white" alt="pre-commit">
    <img src="https://img.shields.io/badge/Taskfile-4d2a85?style=default" alt="Taskfile">
    <img src="https://img.shields.io/badge/Docker-2496ED?style=default&logo=docker&logoColor=white" alt="Docker">
    <img src="https://img.shields.io/badge/Mermaid-ff3670?style=default&logo=mermaid&logoColor=white" alt="Mermaid">
    <img src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=default&logo=Pytest&logoColor=white" alt="Pytest">
    <img src="./docs/img/coverage.svg" alt="coverage">
</p>
<br>

`tidylake` is an agnostic framework for managing data operations in your lakehouse using your favorite tools.

_This project is currently __under active development__, it is currently production tested but future releases will likely include breaking changes._

## Purpose

`tidylake` gives data teams a common ground between:
- Transformation code
- Metadata and contracts
- Operational workflows

It helps you manage the data product lifecycle without locking your project to a single engine, notebook style, or orchestrator.

## Why Use It

The key advantages are:
- Framework agnostic by design: keep using pandas, Spark, Iceberg, and your own stack.
- Metadata-first workflow: manifests act as the single source of truth for schema and semantics.
- Better collaboration across personas: analysts and engineers can work on the same assets with less friction.
- One codebase for interactive and batch work: iterate safely in notebooks and run the same logic in production.
- Built-in structure for automation: lineage discovery, CLI execution, and plugin-based extension points.

## Documentation

For full setup, concepts, and end-to-end examples, go to the documentation:

- [Read the docs](https://tidylake.taidy.io)

## Minimal Example

The docs include complete runnable examples. This is a minimal sketch of what a `tidylake` data product looks like.

Create a manifest (`silver_customers.yml`):

```yaml
data_product:
  name: silver_customers
  description: Customer profile from CRM
  script: silver_customers
  schema:
    properties:
      customer_id:
        type: string
      customer_name:
        type: string
```

Link it to a script (`silver_customers.py`):

```python
import pandas as pd
from tidylake import get_or_create_context

product = get_or_create_context().get_data_product("silver_customers")

@product.add_input()
def bronze_customers():
    return pd.read_parquet("/tmp/bronze_customers")

df = bronze_customers()[["customer_id", "customer_name"]]

@product.set_sink()
def write_silver_customers():
    df.to_parquet("/tmp/silver_customers", index=False)
```

Then use the CLI:

```bash
tidylake list
tidylake run
```

You can extend `tidylake` with plugins to integrate storage, compute, and catalog services from your existing stack.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## License

This project is open source, released under the Apache License, and brought to you by the Taidy team.
