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
    return pd.DataFrame(
        {
            "id": [f"customer_{i}" for i in range(N)],
            "name": ["customer_name" for i in range(N)],
            "active": [random.uniform(0, 1) > 0.5 for i in range(N)],
            "city": [random.choice(["Albacete", "Valencia", "Madrid"]) for i in range(N)],
        }
    )


df_raw_customers = raw_customers()

# %%
df_bronze_customers = df_raw_customers.add_prefix("customer__")


# %%
data_product.set_output_data(df_bronze_customers)
