Tidylake's CLI can help you manage and automate your project, as al alternative you can also interact directly from python using the [SDK](https://github.com/demosense/tidylake/sdk/index.md).

## Basic commands

These commands need to be launched from a tidylake project, for that you must create a valid [context file](https://github.com/demosense/tidylake/context/index.md) that points to one or more data product [manifest files](https://github.com/demosense/tidylake/manifests/index.md).

Every command looks for a `tidylake.yml` file on the root folder of your project, but you can modify this path with the `--file` argument.

### list

Lists the defined data products by following the internal [DAG ordering](https://github.com/demosense/tidylake/context/#dag). Several options can be configured to obtain richer representation of the graph to improve visualization or include in documentations.

```
Usage: tidylake list [OPTIONS]

 Display pipeline structure and visualization.

 Args:     file: Path to the configuration YAML file.     mermaid: Generate Mermaid diagram output.     textual: Launch interactive terminal UI viewer.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --file           TEXT  Path to the YAML file defining processes [default: tidylake.yml]                                                                            │
│ --mermaid              Generate Mermaid diagram                                                                                                                    │
│ --textual              Open Textual viewer                                                                                                                         │
│ --help                 Show this message and exit.                                                                                                                 │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### run

Runs data products scripts in order, this is meant for testing with smaller sets of data or to manage very simple projects that do not require additional orchestration. Can be configured to start and filter subsets of the graph to test only required parts of the process.

This package is not an orchestration tool

We didn't design tidylake as a replacement for orchestration, there are many important functionalities that the package will never cover in the base functionality that should be provided from specialized tools via plugins or by integrating the project with the SDK. Use this command to test and automate early stage projects but plan for a future integration of an orchestration tool when you need to scale things up.

```
uv run tidylake run --help

 Usage: tidylake run [OPTIONS]

 Execute pipeline or individual data product.

 Args:     file: Path to the configuration YAML file.     data product: Name of specific data product to execute. If None, runs entire pipeline.     continue_run:
 Continue execution from the last completed data product.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --file                                 TEXT  Path to the YAML file defining processes [default: tidylake.yml]                                                      │
│ --data-product                         TEXT  Specific data product to run                                                                                          │
│ --continue-run    --no-continue-run          Continue from the last data product [default: no-continue-run]                                                        │
│ --help                                       Show this message and exit.                                                                                           │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### init

Create an scaffold project by seeding base files and configuration. Comes with different flavours but they can be easily adapted to other engines.

```
uv run tidylake init --help

 Usage: tidylake init [OPTIONS]

 Initialize a new project from demo template.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --name          TEXT  Project name [default: my_tidylake_project]                                                                                                  │
│ --engine        TEXT  Engine type: pandas, spark, iceberg [default: pandas]                                                                                        │
│ --help                Show this message and exit.                                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

## Compute Engine commands

This commands are only available when a compute engine has been correctly configured as they interact with catalog and storage systems that are not native to the library. These are meant to encapsulate and abstract under a common framework tasks are are usually repetitive in the management of datalakes.

### schema diff

Prints the differences between the schema in the manifest file and the configured catalog. It uses an intermediate abstraction for data types so your workflow is invariant across projects.

```
uv run tidylake schema diff --help

 Usage: tidylake schema diff [OPTIONS]

 Show schema differences between defined and catalog schemas.

 Args:     file: Path to the configuration YAML file.     data_product: Name of specific data product to check. If None, checks all data products.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --file                TEXT  Path to the YAML file defining processes [default: tidylake.yml]                                                                       │
│ --data-product        TEXT  Specific data product to check                                                                                                         │
│ --help                      Show this message and exit.                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### schema update

Run schema modification in your catalog based on the differences between the manifest file and the schema that is already defined in your catalog. Please use the command in dry run mode and avoid calling `commit` unintentionally as the results can be destructive depending on your compute and storage engine.

```
uv run tidylake schema update --help

 Usage: tidylake schema update [OPTIONS]

 Update schema definitions to match catalog schemas.

 Args:     file: Path to the configuration YAML file.     data_product: Name of specific data product to update. If None, updates all data products.     commit:
 Apply changes to schema files. If False, runs in dry-run mode.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --file                           TEXT  Path to the YAML file defining processes [default: tidylake.yml]                                                            │
│ --data-product                   TEXT  Specific data product to update                                                                                             │
│ --commit          --no-commit          Commit changes [default: no-commit]                                                                                         │
│ --help                                 Show this message and exit.                                                                                                 │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### peek

Renders a sample of the real dataset by accesing the underlying compute engine. This command is optional during the plugin definition as it can pose a data security risk in some scenarios.

```
 uv run tidylake peek --help

 Usage: tidylake peek [OPTIONS]

 Preview data product output data without executing the pipeline.

 Args:     file: Path to the configuration YAML file.     data_product: Name of specific data product to preview.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --file                TEXT  Path to the YAML file defining processes [default: tidylake.yml]                                                                       │
│ --data-product        TEXT  Specific data product to run                                                                                                           │
│ --help                      Show this message and exit.                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
