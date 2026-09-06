import requests
import polars as pl

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
HISTORICAL_SEASON = "2025-26"  # Updated to the most recent completed season
VAASTAV_BASE_URL = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{HISTORICAL_SEASON}"
FPL_API_STATIC = "https://fantasy.premierleague.com/api/bootstrap-static/"
FPL_API_FIXTURES = "https://fantasy.premierleague.com/api/fixtures/?future=1"

# Max "matches worth" of trust carried over from a transferred player's prior-club history
DISCOUNT_CAP = 3.0

# Exponential forgetting: last season's accumulated evidence is discounted by this factor
# (applied to ALL players, not just transfers) so it never permanently anchors the estimate
# as if a player's true rate were static forever -- only this season's data accumulates undecayed.
GAMMA_SEASON = 0.5

# Lower Confidence Bound risk-aversion: how many posterior standard deviations to subtract
# from the mean, so a small-sample fluke (high variance) gets shrunk harder than an estimate
# backed by lots of matches (low variance).
K_RISK_AVERSION = 2.0


def build_data_pipeline():
    print(f"--- 1. Fetching Historical Data ({HISTORICAL_SEASON}) ---")

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

    # C. Calculate Baseline lambda_i and Filter Backups (The 900-Minute Rule)
    # We calculate total season minutes AND the mean points per active match
    player_season_stats = gw_df.group_by("code").agg(
        pl.col("minutes").sum().alias("total_season_minutes"),
        pl.col("total_points").filter(pl.col("minutes") > 0).mean().alias("lambda_i"),
        pl.col("total_points").filter(pl.col("minutes") > 0).sum().alias("alpha_0"),
    )

    # Drop players who didn't play at least 10 full matches to eliminate survivorship bias
    established_players = player_season_stats.filter(
        pl.col("total_season_minutes") >= 900
    )
    lambda_df = established_players.select(["code", "lambda_i"])

    # Unfiltered Gamma-Poisson prior (points per 90 mins) for blending into this season's
    # estimate. Unlike the 900-minute filter above, weak/partial history is fine here --
    # the conjugate update naturally gives a small sample less weight on its own.
    prior_df = player_season_stats.select(
        ["code", "alpha_0", (pl.col("total_season_minutes") / 90).alias("beta_0")]
    )

    # D. Export Historical Training Dataset for GLM Parameter Fitting
    # We only include matches where the player actually played (>0 mins)
    active_gw_df = gw_df.filter(pl.col("minutes") > 0)
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

    events_df = pl.DataFrame(res_static["events"]).sort("id")
    games_played_so_far = events_df.filter(pl.col("finished")).height
    season_start_date = events_df["deadline_time"][0]

    current_players = pl.DataFrame(res_static["elements"]).select(
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

    # Bayesian Gamma-Poisson update: last season's points-per-90 is the prior, updated
    # with this season's actual points/minutes so far (both measured in the same units).
    universe_df = current_players.join(prior_df, on="code", how="left")

    has_history = pl.col("beta_0").is_not_null() & (pl.col("beta_0") > 0)
    prior_mean = (
        pl.when(has_history)
        .then(pl.col("alpha_0") / pl.col("beta_0"))
        .otherwise(pl.lit(1.0))
    )
    beta_0_raw = pl.when(has_history).then(pl.col("beta_0")).otherwise(pl.lit(1.0))

    # Time-decay every player's prior first (exponential forgetting), then additionally cap
    # transferred players' confidence -- whichever discount is more restrictive wins.
    beta_0_decayed = beta_0_raw * GAMMA_SEASON
    is_new_arrival = pl.col("team_join_date").is_not_null() & (
        pl.col("team_join_date") >= pl.lit(season_start_date)
    )
    beta_0_effective = (
        pl.when(is_new_arrival)
        .then(beta_0_decayed.clip(upper_bound=DISCOUNT_CAP))
        .otherwise(beta_0_decayed)
    )
    alpha_0_effective = prior_mean * beta_0_effective

    alpha_post = alpha_0_effective + pl.col("season_points")
    beta_post = beta_0_effective + pl.col("season_minutes") / 90

    # Lower Confidence Bound: shrink towards 0 in proportion to how uncertain the posterior
    # still is (few matches -> high variance -> bigger discount), instead of trusting a
    # fluky small-sample mean at face value.
    posterior_mean = alpha_post / beta_post
    posterior_std = alpha_post.sqrt() / beta_post
    quality_rate = (posterior_mean - K_RISK_AVERSION * posterior_std).clip(
        lower_bound=0.0
    )

    # Discount by how often they've actually started when available, and by any live
    # fitness doubt for the next gameweek.
    start_rate = (
        pl.when(games_played_so_far > 0)
        .then((pl.col("starts") / games_played_so_far).clip(upper_bound=1.0))
        .otherwise(pl.lit(1.0))
    )
    fitness_factor = pl.coalesce(
        [pl.col("chance_of_playing_next_round") / 100.0, pl.lit(1.0)]
    )

    universe_df = universe_df.with_columns(
        (quality_rate * start_rate * fitness_factor).alias("lambda_i")
    ).select(
        ["player_id", "code", "web_name", "team_id", "pos_id", "now_cost", "lambda_i"]
    )

    universe_df.write_csv("current_season_universe.csv")
    print(
        f"Saved 'current_season_universe.csv' ({len(universe_df)} players processed)."
    )

    # -------------------------------------------------------------------------
    print("\n--- 3. Fetching Upcoming Fixtures & Schedule FDR ---")
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
