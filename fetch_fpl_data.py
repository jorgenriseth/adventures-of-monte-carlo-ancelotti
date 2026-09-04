import requests
import polars as pl

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
HISTORICAL_SEASON = "2023-24"  # Season to use for training baseline lambda_i
HISTORICAL_SEASON = "2025-26"  # Season to use for training baseline lambda_i
VAASTAV_BASE_URL = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{HISTORICAL_SEASON}"
FPL_API_STATIC = "https://fantasy.premierleague.com/api/bootstrap-static/"
FPL_API_FIXTURES = "https://fantasy.premierleague.com/api/fixtures/?future=1"


def build_data_pipeline():
    print(f"--- 1. Fetching Historical Data ({HISTORICAL_SEASON}) ---")
    gw_df = pl.read_csv(f"{VAASTAV_BASE_URL}/gws/merged_gw.csv")
    players_raw_df = pl.read_csv(f"{VAASTAV_BASE_URL}/players_raw.csv")
    fixtures_df = pl.read_csv(f"{VAASTAV_BASE_URL}/fixtures.csv")

    # A. Map Opta 'code' to historical gameweek logs via 'element' (historical player_id)
    player_code_lookup = players_raw_df.select(
        [pl.col("id").alias("element"), pl.col("code")]
    )
    gw_df = gw_df.join(player_code_lookup, on="element", how="inner")

    # B. Attach Historical FDR by joining fixture ID and checking Home/Away status
    fixture_fdr_lookup = fixtures_df.select(
        [
            pl.col("id").alias("fixture"),
            pl.col("team_h_difficulty"),
            pl.col("team_a_difficulty"),
        ]
    )
    gw_df = gw_df.join(fixture_fdr_lookup, on="fixture", how="left")

    gw_df = gw_df.with_columns(
        pl.when(pl.col("was_home") == True)
        .then(pl.col("team_h_difficulty"))
        .otherwise(pl.col("team_a_difficulty"))
        .alias("FDR")
    )

    # C. Calculate Baseline lambda_i (Mean points per active match where minutes > 0)
    # Filtering minutes > 0 eliminates training attenuation bias
    active_gw_df = gw_df.filter(pl.col("minutes") > 0)

    lambda_df = active_gw_df.group_by("code").agg(
        pl.col("total_points").mean().alias("lambda_i")
    )

    # D. Export Historical Training Dataset for GLM Parameter Fitting
    training_data = active_gw_df.join(lambda_df, on="code", how="inner").select(
        ["code", "minutes", "total_points", "FDR", "lambda_i"]
    )
    training_data.write_csv("historical_training_data.csv")
    print(
        f"Saved 'historical_training_data.csv' ({len(training_data)} active match logs)."
    )

    # -------------------------------------------------------------------------
    print("\n--- 2. Fetching Current Season Live Player Universe ---")
    res_static = requests.get(FPL_API_STATIC).json()

    current_players = pl.DataFrame(res_static["elements"]).select(
        [
            pl.col("id").alias("player_id"),
            pl.col("code"),
            pl.col("web_name"),
            pl.col("team").alias("team_id"),
            pl.col("element_type").alias("pos_id"),  # 1:GK, 2:DEF, 3:MID, 4:FWD
            pl.col("now_cost"),  # Price scaled by 10
        ]
    )

    # Join historical lambda_i using Opta 'code'
    universe_df = current_players.join(lambda_df, on="code", how="left")

    # -------------------------------------------------------------------------
    print("--- 3. Resolving Cold Start (Price-Position Heuristic for New Arrivals) ---")
    # Calculate average lambda_i for established players grouped by (pos_id, now_cost)
    established_df = universe_df.filter(pl.col("lambda_i").is_not_null())

    price_pos_defaults = established_df.group_by(["pos_id", "now_cost"]).agg(
        pl.col("lambda_i").mean().alias("lambda_imputed_exact")
    )

    pos_defaults = established_df.group_by("pos_id").agg(
        pl.col("lambda_i").mean().alias("lambda_imputed_pos")
    )

    # Impute missing values hierarchically: Exact Price+Pos -> Pos Average -> Absolute Fallback
    universe_df = universe_df.join(
        price_pos_defaults, on=["pos_id", "now_cost"], how="left"
    )
    universe_df = universe_df.join(pos_defaults, on="pos_id", how="left")

    universe_df = universe_df.with_columns(
        pl.coalesce(
            [
                pl.col("lambda_i"),
                pl.col("lambda_imputed_exact"),
                pl.col("lambda_imputed_pos"),
                pl.lit(1.0),  # Absolute fallback default
            ]
        ).alias("lambda_i")
    ).select(
        ["player_id", "code", "web_name", "team_id", "pos_id", "now_cost", "lambda_i"]
    )

    universe_df.write_csv("current_season_universe.csv")
    print(
        f"Saved 'current_season_universe.csv' ({len(universe_df)} players processed)."
    )

    # -------------------------------------------------------------------------
    print("\n--- 4. Fetching Upcoming Fixtures & Schedule FDR ---")
    res_fixtures = requests.get(FPL_API_FIXTURES).json()

    future_fixtures = pl.DataFrame(res_fixtures).filter(pl.col("event").is_not_null())

    # Extract team-level FDR for both Home and Away matches
    home_fdr = future_fixtures.select(
        [
            pl.col("event").alias("gameweek"),
            pl.col("team_h").alias("team_id"),
            pl.col("team_h_difficulty").alias("FDR"),
        ]
    )

    away_fdr = future_fixtures.select(
        [
            pl.col("event").alias("gameweek"),
            pl.col("team_a").alias("team_id"),
            pl.col("team_a_difficulty").alias("FDR"),
        ]
    )

    upcoming_fdr = pl.concat([home_fdr, away_fdr]).sort(["gameweek", "team_id"])
    upcoming_fdr.write_csv("upcoming_fixtures.csv")
    print(f"Saved 'upcoming_fixtures.csv' ({len(upcoming_fdr)} future team fixtures).")


if __name__ == "__main__":
    build_data_pipeline()
