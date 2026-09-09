import polars as pl

# 1. Load gameweek data for 2016-17 or 2017-18
df_gw = pl.read_csv("data/vastaav/data/2016-17/gws/merged_gw.csv", encoding="latin-1")


agg_exprs = [
    pl.col("round").first().alias("event"),
    pl.col("kickoff_time").first(),
    pl.col("opponent_team").filter(pl.col("was_home").not_()).first().alias("team_h"),
    pl.col("opponent_team").filter(pl.col("was_home")).first().alias("team_a"),
]

# 3. Dynamically add match score columns if present in the raw data
for score_col in ["team_h_score", "team_a_score"]:
    if score_col in df_gw.columns:
        agg_exprs.append(pl.col(score_col).first())

# 4. Execute single-pass aggregation and format fixture table
fixtures = df_gw.group_by("fixture").agg(agg_exprs).rename({"fixture": "id"}).sort("id")

print(fixtures.sample(3))
