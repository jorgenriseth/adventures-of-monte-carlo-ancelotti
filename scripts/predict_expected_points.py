import polars as pl
import json


def generate_ev_matrix():
    print("--- 1. Loading Data & Model Parameters ---")

    # 1. Load the player universe (with fully resolved/imputed lambda_i)
    universe_df = pl.read_csv("current_season_universe.csv")

    # 2. Load the upcoming fixtures (FDR for each team per gameweek)
    fixtures_df = pl.read_csv("upcoming_fixtures.csv")

    # 3. Load the learned categorical parameters
    with open("fdr_scaling_parameters.json", "r") as f:
        beta_params = json.load(f)

    print(
        f"Loaded {len(universe_df)} players and {len(fixtures_df['gameweek'].unique())} gameweeks of fixtures."
    )

    print("\n--- 2. Building the Projection Table ---")

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

    print("\n--- 3. Applying the Piecewise Mathematical Projection ---")

    # Apply the mathematical formula: EV = lambda_i * exp(beta_f)
    # The 'when' clause acts as the deterministic bypass to prevent fractional phantom points
    projection_df = projection_df.with_columns(
        pl.when(pl.col("lambda_i") <= 0)
        .then(0.0)
        .otherwise(pl.col("lambda_i") * pl.col("beta_f").exp())
        .alias("expected_points")
    )

    print("\n--- 4. Formatting the EV Matrix for the ILP Solver ---")

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
