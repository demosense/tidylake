The manifests files are the soul of your tidylake project. They serve a dual purpose: it is the documentation for your business assets and the technical data contract enforced in your [script file](https://%3Corg%3E.github.io/tidylake/scripts/index.md).

By centralizing this information, you enable several automated workflows:

- **Validation:** Retrieve schema definitions during pipeline execution to enforce strict typing, mandatory fields, or regular expression checks.
- **Testing:** Use the schema as the blueprint for [synthetic data generation in the compute engine plugin](https://%3Corg%3E.github.io/tidylake/plugins/compute-engine/#synthetic-data).
- **Automation:** Feed product and column metadata directly into [catalog automations in the compute engine plugin](https://%3Corg%3E.github.io/tidylake/plugins/compute-engine/#schema-automation) to keep your SQL metastore in sync with your code.

## Manifest File Schema

At a minimum, a manifest must include the data product's name and the path to its corresponding script file.

```
data_product:
  name: 'bronze_customers' # (1)!
  script: 'bronze_customers' # (2)!
```

1. **Name:** The unique identifier used to reference this product across the project.
1. **Script:** The Python file containing the transformation logic.

### Defining the Schema

While the `schema` section is technically optional, we strongly recommend adding it to every data product. Even if you don't use the automated compute plugins, maintaining a schema manifest is a "gold standard" practice for documentation. It ensures that any team member—or any downstream tool—understands exactly what the data contains without having to read through lines of transformation code.

Currently, tidylake uses a superset of [jsonschema](https://json-schema.org/) to define these structures.

A Note on JSON Schema

We are actively evaluating alternative formats to JSON Schema. While powerful, it can sometimes be challenging to map perfectly across every compute engine (like Spark vs. Snowflake) and storage format.

```
data_product:
  name: 'bronze_customers'
  script: 'bronze_customers'
  schema:
    type: 'object'
    properties:
      customer__id:
        type: 'string'
      customer__name:
        type: 'string'
      customer__active:
        type: 'boolean'
      customer__city:
        type: 'string'
```
