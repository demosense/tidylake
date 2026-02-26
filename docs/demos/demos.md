---
title: demos
---

These examples provide production-ready scenarios featuring specific combinations of adapters and engines. Use them to jumpstart your project or to see the tidylake design principles in action.

- [**Pandas Local**:](./pandas-local.md) The "Bare Minimum" blueprint. This demo showcases a basic project without a compute engine plugin, demonstrating how to encapsulate standard pandas logic and local filesystem I/O within the tidylake framework.

- [**Pandas pyiceberg**:](./pandas-pyiceberg.md) An infrastructure-agnostic example. This blueprint features a full Compute Engine implementation, using  to manage both storage and cataloging on a local filesystem. It is the perfect starting point for building a local Lakehouse.

- [**Pyspark**:](./pyspark.md) A cluster-ready implementation. This demo uses PySpark over Docker to show how the Compute Engine plugin encapsulates session management. It demonstrates that even a complex framework like Apache Spark can be used in clean, readable scripts without infrastructure leaking into your business logic.