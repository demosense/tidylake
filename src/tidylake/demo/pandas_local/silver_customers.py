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
