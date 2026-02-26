# %%
import random

import pandas as pd

from tidylake import get_or_create_context

data_product = get_or_create_context().get_data_product("bronze_customers")

# %%
# generate N random records
N = 10


@data_product.add_input(raw=True)
def raw_customers():
    # TODO: Use a getter for this
    return data_product.compute_engine.spark.createDataFrame(
        pd.DataFrame(
            {
                "customer_id": [f"cust_{i}" for i in range(N)],
                "customer_name": [f"Customer {i}" for i in range(N)],
                "customer_age": [random.randint(18, 70) for _ in range(N)],
                "customer_email": [f"customer_{i}@example.com" for i in range(N)],
            }
        )
    )


df_raw_customers = raw_customers()

# %%
df_bronze_customers = df_raw_customers


# %%
data_product.set_output_data(df_bronze_customers)

# @data_product.set_sink()
# def write_bronze_customers():
#     return (
#         df_bronze_customers.write.option("path", "/tmp/bronze_customers")
#         .mode("overwrite")
#         .saveAsTable("bronze_customers")
#     )
