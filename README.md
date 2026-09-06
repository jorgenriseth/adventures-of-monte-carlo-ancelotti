# myfpl

FPL squad optimizer: fetches player/fixture data, fits a GLM to scale each
player's expected score by fixture difficulty, projects expected points per
gameweek, then solves for an optimal squad over a rolling horizon.

## Usage

```bash
# 1. Rebuild the data pipeline (historical training data, live player universe, upcoming fixtures)
uv run scripts/fetch_fpl_data.py

# 2. Refit the FDR scaling GLM parameters from historical data
uv run scripts/train_fdr_model.py

# 3. Project expected points per player per gameweek
uv run scripts/predict_expected_points.py

# 4. Fetch your current team state (bank, squad, free transfers) and save it to team_state.json
uv run scripts/fetch_team_state.py --manager-id 2872027

# 5. Optimize starting from that saved team state
uv run scripts/optimize_fpl_squad.py --horizon 5
```

Or for a pre-season draft instead of an existing squad (skips step 4):

```bash
uv run scripts/optimize_fpl_squad.py --draft --horizon 5
```

If you set `export UV_ENV_FILE=.env` (with `FPL_MANAGER_ID=...` in a `.env`
file) once per shell session, step 4 simplifies to:

```bash
uv run scripts/fetch_team_state.py
```

Step 4 opens `fantasy.premierleague.com` in your browser (default
`--login-method browser`) and prompts you to press Enter once you've copied a
`Copy as cURL` capture of the `/api/my-team/...` request to your clipboard.
Fetching is a separate, one-off step from optimizing on purpose — re-run it
whenever your real squad changes, then iterate on `--horizon`/`--bank`/etc. in
step 5 as many times as you like without re-authenticating each time.

`team_state.json` is plain JSON with a `web_name` per squad player, so you can
open it directly to confirm it fetched the right squad, or hand-edit it (e.g.
for testing a hypothetical transfer) before passing it to step 5 via
`--team-state-json <path>` (defaults to `team_state.json`).

