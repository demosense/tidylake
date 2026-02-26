# %%
import random

import pandas as pd

from tidylake import get_or_create_context

data_product = get_or_create_context().get_data_product("bronze_profile")

# %%
# generate N random records
N = 10


@data_product.add_input(raw=True)
def raw_profile():
    return pd.DataFrame(
        {
            "id": [f"customer_{i}" for i in range(N)],
            "account": [random.choice(["free", "premium"]) for i in range(N)],
        }
    )


df_raw_profile = raw_profile()


# %%
df_bronze_profile = df_raw_profile.add_prefix("profile__")


# %%
@data_product.set_sink()
def write_bronze_profile():
    return df_bronze_profile.to_parquet("/tmp/bronze_profile", index=False)
