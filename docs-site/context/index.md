The context file is the entry point for every tidylake project. Whether you are using the [CLI](https://github.com/demosense/tidylake/cli/index.md) or the [SDK](https://github.com/demosense/tidylake/sdk/index.md), this file is the first thing parsed during a command or library import.

It defines how the package behaves and can be extended with custom functionality through then [plugin system](https://github.com/demosense/tidylake/plugins/overview/index.md).

## Defining Your Data Products

At its simplest, a valid context file requires only a project name and a list of your data product manifests:

```
tidylake:
    name: TestContextFile
    include_data_products:
        - bronze_customers.yml
        - silver_customers.yml
        - gold_customers.yml
```

When this file is loaded, tidylake scans for the corresponding [manifest files](https://github.com/demosense/tidylake/manifests/index.md). The only requirement is that these files exist and follow the standard YAML schema for manifests.

### Building the Dependency DAG

The order in which you list products in the context file **does not matter**. Instead, the execution order is determined by the internal dependencies defined within your [script files](https://github.com/demosense/tidylake/scripts/index.md).

Tidylake automatically builds a Directed Acyclic Graph (DAG) of your entire project. If it detects a dependency cycle (where Product A depends on Product B, which in turn depends on Product A), the system will fail early with a clear error.

Keep it tidy!

Because tidylake handles the execution order for you, you are free to organize the list in your context file alphabetically or by "tier" (Bronze, Silver, Gold) to make it easier for your team to maintain.

## Context File Reference

```
tidylake:
    type: object
    properties:
        name:
            type: str
            description: Name of your project
        include_data_products:
            type: array
            description: List to the files of data product manifest to include in your project
            items:
                type: string
        plugins:
            type: object
            description: Plugin Configuration
            properties:
                compute_engine:
                    type: object
                    description: Configuration for the compute engine plugin
                    properties:
                        plugin_path:
                            type: string
                            description: Path to the python file that defines the plugin. Takes precedence
                        plugin_module: 
                            type: string
                            description: Path to the python module that contains the plugin
                        plugin_class_name: 
                            type: string
                            description: Name of the python path inside file or module
```
