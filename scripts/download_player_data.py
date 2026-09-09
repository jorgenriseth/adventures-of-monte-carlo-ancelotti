# %%
import requests
from pathlib import Path

import polars as pl

from myfpl.constants import URL_VASTAAV_FPL_DATA, DATA_DIR


# %%
SEASONS = (
    "2016-17",
    "2017-18",
    "2018-19",
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
    "2025-26",
)
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
for season in SEASONS:
    response = requests.get(f"{URL_VASTAAV_FPL_DATA}/{season}/players_raw.csv")
    response.raise_for_status()
    Path(f"{DATA_DIR}/players_raw_{season}.csv").write_text(response.text)
# %%
df_all_players_raw = pl.concat(
    (
        pl.read_csv(
            f"{DATA_DIR}/players_raw_{season}.csv", null_values=("None")
        ).with_columns(pl.lit(season).alias("season"))
        for season in SEASONS
    ),
    how="diagonal_relaxed",
)
PLAYER_KEYS = (
    "code",
    "web_name",
    "first_name",
    "second_name",
    "element_type",
    "season",
    "team",
    "team_code",
    "id",
)
df = df_all_players_raw[PLAYER_KEYS].rename(
    {
        "id": "player_season_id",
    }
)
df.unique("code")


# %%
df.filter(~pl.col("has_temporary_code"))

# %%
df.filter(pl.col("web_name") == "Salah")

# df_all_players

# %%
df_all_players_raw.unique("code")
# %%
df = df_all_players
df.unique("code")

# %%

players_list = df.unique("code")[keys_list]
players_list
# %%
players_list.filter(pl.col("opta_code").is_null()).group_by("season").agg(
    pl.count()
).sort("season")
# %%
players_list.group_by("season").agg(pl.count()).sort("season")

# %%

players_list["web_name", "code", "opta_code"].with_columns(
    pl.col("opta_code")
    .str.contains(pl.col("code").cast(pl.String))
    .alias("opta_code_container")
).filter(~pl.col("opta_code").is_null() & ~pl.col("opta_code_container"))

# %%
df.filter(pl.col("web_name") == "Salah")[
    "code", "opta_code", "second_name", "first_name", "web_name", "season"
]

# %%
