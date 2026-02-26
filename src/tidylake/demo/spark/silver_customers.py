# %%
from tidylake import get_or_create_context

data_product = get_or_create_context().get_data_product("silver_customers")


# %%
df_bronze_customers = data_product.read_input("bronze_customers")


# %%
df_silver_customers = (
    df_bronze_customers
    # .rename(
    #     columns={
    #         "customer__id": "customer_id",
    #         "customer__name": "customer_name",
    #         "customer__city": "customer_city",
    #     }
    # )
    # .assign(
    #     customer_city=lambda df: df["customer_city"].str.upper(),
    #     customer_name=lambda df: df["customer_name"].str.title(),
    # )
    # .sort_values(by="customer_id")[
    #     ["customer_id", "customer_name", "customer_city", "customer_account"]
    # ]
)


# %%
data_product.set_output_data(df_silver_customers)
