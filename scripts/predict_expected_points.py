import json
from datetime import UTC, datetime

import polars as pl

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

# Warn (rather than silently trust) fitness/rotation inputs older than this many hours
STALE_DATA_HOURS = 6


def build_player_universe():
    print("--- 1. Loading Raw Player Data & Priors ---")
    current_players = pl.read_csv("current_players_raw.csv")
    prior_df = pl.read_csv("historical_player_priors.csv")

    with open("fetch_metadata.json", "r") as f:
        fetch_metadata = json.load(f)
    games_played_so_far = fetch_metadata["games_played_so_far"]
    season_start_date = fetch_metadata["season_start_date"]

    fetched_at = datetime.fromisoformat(fetch_metadata["fetched_at"])
    age_hours = (datetime.now(UTC) - fetched_at).total_seconds() / 3600
    if age_hours > STALE_DATA_HOURS:
        print(
            f"WARNING: fetch_metadata.json is {age_hours:.1f}h old (fetched {fetched_at.isoformat()}). "
            "Fitness/rotation-based lambda_i may be stale -- rerun fetch_fpl_data.py."
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

    # season_points can go negative (e.g. own goals/red cards), but alpha_post is a Gamma
    # shape parameter and must stay non-negative for the sqrt below to be defined.
    alpha_post = (alpha_0_effective + pl.col("season_points")).clip(lower_bound=0.0)
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
    return universe_df


def generate_ev_matrix():
    # 1. Resolve/impute lambda_i for the live player universe
    universe_df = build_player_universe()

    print("\n--- 2. Loading Fixtures & Model Parameters ---")

    # 2. Load the upcoming fixtures (FDR for each team per gameweek)
    fixtures_df = pl.read_csv("upcoming_fixtures.csv")

    # 3. Load the learned categorical parameters
    with open("fdr_scaling_parameters.json", "r") as f:
        beta_params = json.load(f)

    print(
        f"Loaded {len(universe_df)} players and {len(fixtures_df['gameweek'].unique())} gameweeks of fixtures."
    )

    print("\n--- 3. Building the Projection Table ---")

    # Join fixtures onto the player universe based on team_id
    # This gives us a row for every player-match combination in the upcoming horizon
    projection_df = universe_df.join(fixtures_df, on="team_id", how="inner")

    # Map the categorical FDR to its learned beta multiplier using the JSON dictionary.
    # We cast FDR to string so it safely matches the JSON keys (e.g., "2", "4").
    # If an FDR is missing (like FDR 3, our neutral reference), we default it to 0.0.
    projection_df = projection_df.with_columns(
        pl.col("FDR")
        .cast(pl.Utf8)
        .replace(beta_params, default=0.0)
        .cast(pl.Float64)
        .alias("beta_f")
    )

    print("\n--- 4. Applying the Piecewise Mathematical Projection ---")

    # Apply the mathematical formula: EV = lambda_i * exp(beta_f)
    # The 'when' clause acts as the deterministic bypass to prevent fractional phantom points
    projection_df = projection_df.with_columns(
        pl.when(pl.col("lambda_i") <= 0)
        .then(0.0)
        .otherwise(pl.col("lambda_i") * pl.col("beta_f").exp())
        .alias("expected_points")
    )

    print("\n--- 5. Formatting the EV Matrix for the ILP Solver ---")

    # The solver expects a matrix where rows = players, columns = gameweeks.
    # We pivot the dataset to achieve this format.
    ev_matrix = projection_df.pivot(
        values="expected_points",
        index=["player_id", "web_name", "pos_id", "now_cost", "team_id"],
        on="gameweek",
        aggregate_function="first",
    )

    # Fill any missing gameweek projections (e.g., if a team has a blank gameweek) with 0.0
    # We identify gameweek columns by checking if the column name is a digit
    gameweek_cols = [col for col in ev_matrix.columns if col.isdigit()]
    ev_matrix = ev_matrix.with_columns(
        [pl.col(gw).fill_null(0.0) for gw in gameweek_cols]
    )

    # Rename numerical columns to explicit GW1, GW2, etc. for cleaner downstream code
    ev_matrix = ev_matrix.rename({gw: f"GW{gw}" for gw in gameweek_cols})

    ev_matrix.write_csv("expected_points_matrix.csv")
    print(f"Success! Saved 'expected_points_matrix.csv' with shape {ev_matrix.shape}.")

    return ev_matrix


if __name__ == "__main__":
    generate_ev_matrix()
