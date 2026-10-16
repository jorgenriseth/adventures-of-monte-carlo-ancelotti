import polars as pl
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import json


def train_categorical_glm():
    print("--- 1. Deriving Baseline lambda_i and Priors from Raw Match Logs ---")
    match_logs = pl.read_csv("historical_match_logs.csv")

    # Calculate total season minutes AND the mean points per active match
    player_season_stats = match_logs.group_by("code").agg(
        pl.col("minutes").sum().alias("total_season_minutes"),
        pl.col("total_points").filter(pl.col("minutes") > 0).mean().alias("lambda_i"),
        pl.col("total_points").filter(pl.col("minutes") > 0).sum().alias("alpha_0"),
    )

    # Drop players who didn't play at least 10 full matches to eliminate survivorship bias
    established_players = player_season_stats.filter(
        pl.col("total_season_minutes") >= 900
    )
    lambda_df = established_players.select(["code", "lambda_i"])

    # Unfiltered Gamma-Poisson prior (points per 90 mins) for predict_expected_points.py's
    # Bayesian update. Unlike the 900-minute filter above, weak/partial history is fine
    # here -- the conjugate update naturally gives a small sample less weight on its own.
    prior_df = player_season_stats.select(
        ["code", "alpha_0", (pl.col("total_season_minutes") / 90).alias("beta_0")]
    )
    prior_df.write_csv("historical_player_priors.csv")
    print(f"Saved 'historical_player_priors.csv' ({len(prior_df)} players).")

    print("\n--- 2. Loading and Cleaning Training Data ---")
    # Only matches where the player actually played (>0 mins), with lambda_i attached
    active_match_logs = match_logs.filter(pl.col("minutes") > 0)
    df = active_match_logs.join(lambda_df, on="code", how="inner").select(
        ["code", "minutes", "total_points", "FDR", "lambda_i"]
    )

    # 1. mathematically protect the log() offset: lambda_i must be strictly > 0
    df = df.filter(pl.col("lambda_i") > 0)

    # 2. Negative Binomial requires non-negative integers (clip negatives to 0)
    df = df.with_columns(
        pl.when(pl.col("total_points") < 0)
        .then(0)
        .otherwise(pl.col("total_points"))
        .alias("total_points")
    )

    # Convert to Pandas for statsmodels compatibility
    pdf = df.to_pandas()

    print(f"Prepared {len(pdf)} active match records for training.")

    print("\n--- 3. Constructing the Categorical Matrix ---")
    # We dynamically find all FDR categories present in the data (usually 2, 3, 4, 5)
    fdr_levels = sorted(pdf["FDR"].unique())

    # We remove FDR 3 from the list of dummies, making it the mathematical Reference Category
    dummy_cols = [f for f in fdr_levels if f != 3]

    # Create manual dummy (indicator) columns for the remaining FDR levels
    for f in dummy_cols:
        col_name = f"FDR_{f}"
        pdf[col_name] = (pdf["FDR"] == f).astype(int)

    print(f"Reference Category: FDR 3")
    print(f"Dummy Variables Created: {[f'FDR_{f}' for f in dummy_cols]}")

    print("\n--- 4. Fitting the Negative Binomial GLM ---")
    # Calculate the exact mathematical offset: log(lambda_i)
    offset_array = np.log(pdf["lambda_i"])

    # Build the formula dynamically.
    # The '- 1' strictly removes the intercept so the model relies purely on the offset.
    formula = "total_points ~ " + " + ".join([f"FDR_{f}" for f in dummy_cols]) + " - 1"
    print(f"Model Formula: {formula} + offset(log(lambda_i))")

    # Fit the Negative Binomial model via Maximum Likelihood Estimation (MLE)
    # smf.negativebinomial simultaneously estimates our betas and the dispersion parameter (alpha)
    model = smf.negativebinomial(formula=formula, data=pdf, offset=offset_array)

    result = model.fit(disp=False)  # disp=False hides the raw optimization console spam
    print("\n" + str(result.summary()))

    print("\n--- 5. Exporting Learned Parameters ---")
    # Extract the fitted beta parameters for each FDR category
    learned_betas = {}
    for f in dummy_cols:
        col_name = f"FDR_{f}"
        if col_name in result.params:
            learned_betas[str(f)] = result.params[col_name]

    # Explicitly hardcode FDR 3 to equal 0.0 (multiplier = exp(0) = 1.0)
    learned_betas["3"] = 0.0

    # Export parameters for the projection/prediction script
    with open("fdr_scaling_parameters.json", "w") as outfile:
        json.dump(learned_betas, outfile, indent=4)

    print("Saved 'fdr_scaling_parameters.json'. Ready for projection!")


if __name__ == "__main__":
    train_categorical_glm()
