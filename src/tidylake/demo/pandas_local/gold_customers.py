# %%
import pandas as pd

from tidylake import get_or_create_context

data_product = get_or_create_context().get_data_product("gold_customers")


# %%
@data_product.add_input()
def silver_customers():
    return pd.read_parquet("/tmp/silver_customers")


df_silver_customers = silver_customers()

# %%
df_gold_customers = df_silver_customers.groupby("customer_city").agg(
    total_customers=("customer_id", "count"),
)


# %%
@data_product.set_sink()
def write_gold_customers():
    return df_gold_customers.to_parquet("/tmp/gold_customers", index=False)
