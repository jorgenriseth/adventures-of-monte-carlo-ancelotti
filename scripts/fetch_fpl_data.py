import json
from datetime import UTC, datetime

import polars as pl
import requests

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
HISTORICAL_SEASON = "2025-26"  # Updated to the most recent completed season
VAASTAV_BASE_URL = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{HISTORICAL_SEASON}"
FPL_API_STATIC = "https://fantasy.premierleague.com/api/bootstrap-static/"
FPL_API_FIXTURES = "https://fantasy.premierleague.com/api/fixtures/?future=1"


def build_data_pipeline():
    print(f"--- 1. Fetching Historical Match Logs ({HISTORICAL_SEASON}) ---")

    # Safely handle FPL's weird string formats for missing data
    csv_kwargs = {"null_values": ["None", "NA", ""], "infer_schema_length": 10000}

    gw_df = pl.read_csv(f"{VAASTAV_BASE_URL}/gws/merged_gw.csv", **csv_kwargs)
    players_raw_df = pl.read_csv(f"{VAASTAV_BASE_URL}/players_raw.csv", **csv_kwargs)
    fixtures_df = pl.read_csv(f"{VAASTAV_BASE_URL}/fixtures.csv", **csv_kwargs)

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

    # C. Export the raw per-match log; lambda_i/priors are derived downstream in train_fdr_model.py
    historical_match_logs = gw_df.select(["code", "minutes", "total_points", "FDR"])
    historical_match_logs.write_csv("historical_match_logs.csv")
    print(
        f"Saved 'historical_match_logs.csv' ({len(historical_match_logs)} match logs)."
    )

    # -------------------------------------------------------------------------
    print("\n--- 2. Fetching Current Season Live Player Universe ---")
    res_static = requests.get(FPL_API_STATIC).json()

    events_df = pl.DataFrame(res_static["events"], infer_schema_length=None).sort("id")
    games_played_so_far = events_df.filter(pl.col("finished")).height
    season_start_date = events_df["deadline_time"][0]

    current_players = pl.DataFrame(
        res_static["elements"], infer_schema_length=None
    ).select(
        [
            pl.col("id").alias("player_id"),
            pl.col("code"),
            pl.col("web_name"),
            pl.col("team").alias("team_id"),
            pl.col("element_type").alias("pos_id"),  # 1:GK, 2:DEF, 3:MID, 4:FWD
            pl.col("now_cost"),  # Price scaled by 10 (e.g., 40 = £4.0m)
            pl.col("total_points").alias("season_points"),
            pl.col("minutes").alias("season_minutes"),
            pl.col("starts"),
            pl.col("chance_of_playing_next_round").cast(pl.Float64),
            pl.col("team_join_date"),
        ]
    )

    # Raw fields only; the Bayesian quality/lambda_i model lives in predict_expected_points.py
    current_players.write_csv("current_players_raw.csv")
    print(f"Saved 'current_players_raw.csv' ({len(current_players)} players fetched).")

    # Scalars needed by the downstream model, plus a timestamp to detect stale fetches
    fetch_metadata = {
        "fetched_at": datetime.now(UTC).isoformat(),
        "games_played_so_far": games_played_so_far,
        "season_start_date": season_start_date,
    }
    with open("fetch_metadata.json", "w") as outfile:
        json.dump(fetch_metadata, outfile, indent=4)
    print("Saved 'fetch_metadata.json'.")

    # -------------------------------------------------------------------------
    print("\n--- 3. Fetching Upcoming Fixtures & Schedule FDR ---")
    res_fixtures = requests.get(FPL_API_FIXTURES).json()

    future_fixtures = pl.DataFrame(res_fixtures, infer_schema_length=None).filter(
        pl.col("event").is_not_null()
    )

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
