import argparse

import polars as pl
import pulp

from myfpl.team_state import TeamState


def solve_fpl_ilp(
    matrix_csv: str = "expected_points_matrix.csv",
    starting_bank: float = 100.0,  # Pre-season draft budget in £ millions (ignored if team_state given)
    horizon_length: int | None = None,  # Number of gameweeks (None = full matrix)
    max_banked_transfers: int = 5,  # Up to 5 banked transfers
    team_state: TeamState | None = None,  # None triggers Pre-Season Draft mode
    time_limit: int = 60,  # Solver timeout in seconds
    wildcard_gw: int | None = None,  # Real GW number (e.g. 8) where Wildcard is played
):
    print("--- 1. Loading Expected Value Matrix ---")
    df = pl.read_csv(matrix_csv)

    # Extract all gameweek column names (GW1, GW2, etc.)
    all_gw_cols = [c for c in df.columns if c.startswith("GW")]

    # Slice gameweeks if horizon_length argument is passed
    if horizon_length is not None and horizon_length > 0:
        gw_cols = all_gw_cols[:horizon_length]
        print(
            f"Horizon specified: Restricting optimization to first {len(gw_cols)} gameweeks."
        )
    else:
        gw_cols = all_gw_cols
        print(f"No horizon specified: Using full matrix ({len(gw_cols)} gameweeks).")

    T = list(range(1, len(gw_cols) + 1))

    # Resolve the real-world wildcard gameweek to its position in this horizon
    wildcard_t = None
    if wildcard_gw is not None:
        wildcard_col = f"GW{wildcard_gw}"
        if wildcard_col not in gw_cols:
            raise ValueError(
                f"--wildcard-gw {wildcard_gw} is outside the optimized horizon "
                f"({gw_cols[0]}-{gw_cols[-1]})."
            )
        wildcard_t = gw_cols.index(wildcard_col) + 1
        print(f"Wildcard active: {wildcard_col} (hits waived, transfers unlimited).")

    # Scale prices to integers (tenths of a million, e.g., £10.0m = 100)
    df = df.with_columns((pl.col("now_cost")).cast(pl.Int64).alias("price"))

    players = df["player_id"].to_list()
    p_to_idx = {pid: idx for idx, pid in enumerate(players)}

    # Extract static mapping dictionaries
    price = {p: df.filter(pl.col("player_id") == p)["price"][0] for p in players}
    pos_id = {p: df.filter(pl.col("player_id") == p)["pos_id"][0] for p in players}
    team_id = {p: df.filter(pl.col("player_id") == p)["team_id"][0] for p in players}
    web_name = {p: df.filter(pl.col("player_id") == p)["web_name"][0] for p in players}

    # Expected points dictionary E[i, t]
    E = {}
    for t_idx, gw_col in enumerate(gw_cols, start=1):
        points_list = df[gw_col].to_list()
        for p in players:
            E[p, t_idx] = points_list[p_to_idx[p]]

    # Index subsets
    I = players
    Clubs = list(set(team_id.values()))

    # Owned players sell at their held selling_price; everyone else sells at current price
    owned_selling_price = (
        {m.player_id: m.selling_price for m in team_state.squad}
        if team_state is not None
        else {}
    )
    sell_price = {i: owned_selling_price.get(i, price[i]) for i in I}

    # Cash in the bank before GW1: real bank mid-season, full budget for a pre-season draft
    initial_bank = (
        team_state.bank if team_state is not None else int(round(starting_bank * 10))
    )

    print(
        f"Loaded {len(I)} players across {len(T)} gameweeks ({gw_cols[0]} to {gw_cols[-1]})."
    )

    print("\n--- 2. Instantiating ILP Decision Variables ---")
    prob = pulp.LpProblem("FPL_Rolling_Horizon_Optimization", pulp.LpMaximize)

    # Decision Variables
    x = pulp.LpVariable.dicts(
        "x", ((i, t) for i in I for t in T), cat=pulp.LpBinary
    )  # Squad
    y = pulp.LpVariable.dicts(
        "y", ((i, t) for i in I for t in T), cat=pulp.LpBinary
    )  # Starting XI
    c = pulp.LpVariable.dicts(
        "c", ((i, t) for i in I for t in T), cat=pulp.LpBinary
    )  # Captain
    u = pulp.LpVariable.dicts(
        "u", ((i, t) for i in I for t in T), cat=pulp.LpBinary
    )  # Buy
    v = pulp.LpVariable.dicts(
        "v", ((i, t) for i in I for t in T), cat=pulp.LpBinary
    )  # Sell

    Bank = pulp.LpVariable.dicts("Bank", (t for t in T), lowBound=0, cat=pulp.LpInteger)
    K = pulp.LpVariable.dicts("K", (t for t in T), lowBound=0, cat=pulp.LpInteger)
    H = pulp.LpVariable.dicts("H", (t for t in T), lowBound=0, cat=pulp.LpInteger)
    S = pulp.LpVariable.dicts("S", (t for t in T), lowBound=0, cat=pulp.LpInteger)
    w = pulp.LpVariable.dicts("w", (t for t in T), lowBound=0, cat=pulp.LpInteger)

    # --- 3. Objective Function ---
    bench_weight = 0.01  # Microscopic tie-breaker weight
    # x[i,t] - y[i,t] mathematically isolates the bench players (1 - 0 = 1).
    # If they start, it evaluates to (1 - 1 = 0), so the bench weight is ignored.
    prob += pulp.lpSum(
        E[i, t]
        * (
            y[i, t]  # 1.0x multiplier for starting
            + c[i, t]  # +1.0x multiplier for captaincy
            + bench_weight * (x[i, t] - y[i, t])  # 0.01x multiplier for bench
        )
        for i in I
        for t in T
    ) - pulp.lpSum(4 * H[t] for t in T)

    print("--- 4. Adding Constraints ---")

    # Initial State at t=0
    owned_ids = (
        {m.player_id for m in team_state.squad} if team_state is not None else set()
    )
    x_0 = {i: (1 if i in owned_ids else 0) for i in I}

    for t in T:
        # 1. Squad Mass-Balance & Mutual Exclusivity
        for i in I:
            if t == 1:
                prob += x[i, t] == x_0[i] + u[i, t] - v[i, t]
            else:
                prob += x[i, t] == x[i, t - 1] + u[i, t] - v[i, t]

            prob += u[i, t] + v[i, t] <= 1

        # 2. 15-Man Squad Constraints
        prob += pulp.lpSum(x[i, t] for i in I) == 15
        prob += pulp.lpSum(x[i, t] for i in I if pos_id[i] == 1) == 2  # GK
        prob += pulp.lpSum(x[i, t] for i in I if pos_id[i] == 2) == 5  # DEF
        prob += pulp.lpSum(x[i, t] for i in I if pos_id[i] == 3) == 5  # MID
        prob += pulp.lpSum(x[i, t] for i in I if pos_id[i] == 4) == 3  # FWD

        for club in Clubs:
            prob += pulp.lpSum(x[i, t] for i in I if team_id[i] == club) <= 3

        # 3. Starting XI Formation Constraints
        for i in I:
            prob += y[i, t] <= x[i, t]

        prob += pulp.lpSum(y[i, t] for i in I) == 11
        prob += pulp.lpSum(y[i, t] for i in I if pos_id[i] == 1) == 1  # Exactly 1 GK
        prob += pulp.lpSum(y[i, t] for i in I if pos_id[i] == 2) >= 3  # 3 to 5 DEF
        prob += pulp.lpSum(y[i, t] for i in I if pos_id[i] == 2) <= 5
        prob += pulp.lpSum(y[i, t] for i in I if pos_id[i] == 3) >= 2  # 2 to 5 MID
        prob += pulp.lpSum(y[i, t] for i in I if pos_id[i] == 3) <= 5
        prob += pulp.lpSum(y[i, t] for i in I if pos_id[i] == 4) >= 1  # 1 to 3 FWD
        prob += pulp.lpSum(y[i, t] for i in I if pos_id[i] == 4) <= 3

        # 4. Captaincy Constraints
        for i in I:
            prob += c[i, t] <= y[i, t]
        prob += pulp.lpSum(c[i, t] for i in I) == 1

        # 5. Budget Conservation (cash-flow: sells add money, buys spend it)
        prev_bank = initial_bank if t == 1 else Bank[t - 1]
        prob += Bank[t] == (
            prev_bank
            + pulp.lpSum(sell_price[i] * v[i, t] for i in I)
            - pulp.lpSum(price[i] * u[i, t] for i in I)
        )

        # 6. Transfer Rollover & Hit Mechanics
        prob += K[t] == pulp.lpSum(u[i, t] for i in I)
        prob += S[t] <= max_banked_transfers

        if t == 1:
            if team_state is None:
                # Pre-season draft mode
                prob += H[1] == 0
                prob += S[1] == 0
            elif t == wildcard_t:
                # Wildcard bypasses the free-transfer counter entirely: no hits,
                # and the banked-transfer rollover accrues as if K[1] were 0.
                prob += H[1] == 0
                prob += S[1] + w[1] == team_state.free_transfers
            else:
                prob += K[1] + S[1] + w[1] - H[1] == team_state.free_transfers
        elif t == wildcard_t:
            prob += H[t] == 0
            prob += S[t] + w[t] == S[t - 1] + 1
        else:
            prob += K[t] + S[t] + w[t] - H[t] == S[t - 1] + 1

    print("--- 5. Solving Integer Linear Program ---")
    # Configured with status output (msg=True) and early exit limits
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit)
    status = prob.solve(solver)

    print(f"\nSolver Status: {pulp.LpStatus[status]}")
    print(
        f"Optimal Total Expected Score (Z): {pulp.value(prob.objective):.2f} points\n"
    )

    # --- 6. Output Plan ---
    for t in T:
        gw_name = gw_cols[t - 1]

        # Calculate Gameweek Expected Points
        gw_gross_ev = sum(E[i, t] * (y[i, t].varValue + c[i, t].varValue) for i in I)
        gw_hit_cost = int(H[t].varValue) * 4
        gw_net_ev = gw_gross_ev - gw_hit_cost

        wildcard_tag = " [WILDCARD]" if t == wildcard_t else ""
        print(f"==========================================")
        print(f"            {gw_name} PLAN{wildcard_tag}")
        print(f"    Expected Points: {gw_gross_ev:.2f} (Net: {gw_net_ev:.2f})")
        print(f"==========================================")

        buys = [web_name[i] for i in I if u[i, t].varValue > 0.5]
        sells = [web_name[i] for i in I if v[i, t].varValue > 0.5]

        if t == 1 and team_state is None:
            print("Action: Pre-Season Draft Assembled")
        else:
            print(f"Transfers In  ({len(buys)}): {', '.join(buys) if buys else 'None'}")
            print(
                f"Transfers Out ({len(sells)}): {', '.join(sells) if sells else 'None'}"
            )
            if t == wildcard_t:
                print("Hits Taken: 0 (Wildcard active, free transfers unaffected)")
            else:
                print(
                    f"Hits Taken: {int(H[t].varValue)} (-{gw_hit_cost} pts) | Banked FTs: {int(S[t].varValue)}"
                )

        starters = [i for i in I if y[i, t].varValue > 0.5]
        bench = [i for i in I if (x[i, t].varValue > 0.5 and y[i, t].varValue <= 0.5)]
        captain = [i for i in I if c[i, t].varValue > 0.5][0]

        print(f"\nStarting XI:")
        for pos_num, pos_name in [(1, "GK"), (2, "DEF"), (3, "MID"), (4, "FWD")]:
            pos_starters = [i for i in starters if pos_id[i] == pos_num]
            names = []
            for i in pos_starters:
                cap_str = " (C)" if i == captain else ""
                names.append(f"{web_name[i]}{cap_str} [{E[i, t]:.1f}]")
            print(f"  {pos_name}: {', '.join(names)}")

        print(f"\nBench:")
        bench_str = [f"{web_name[i]} [{E[i, t]:.1f}]" for i in bench]
        print(f"  {', '.join(bench_str)}")

        rem_bank = Bank[t].varValue / 10.0
        print(f"\nBank Remaining: £{rem_bank:.1f}m\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize FPL squad via ILP.")
    parser.add_argument(
        "--horizon",
        "-H",
        type=int,
        default=None,
        help="Number of gameweeks to optimize over (default: full matrix).",
    )
    parser.add_argument(
        "--matrix",
        type=str,
        default="expected_points_matrix.csv",
        help="Path to expected points matrix CSV.",
    )
    parser.add_argument(
        "--bank",
        type=float,
        default=100.0,
        help="Pre-season draft budget in £m (default: 100.0). Ignored in mid-season mode.",
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        help="Solver time limit in seconds (default: None).",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Run a pre-season draft. Mutually exclusive with --team-state-json.",
    )
    parser.add_argument(
        "--team-state-json",
        type=str,
        default="team_state.json",
        help="Path to a TeamState JSON file (produced by scripts/fetch_team_state.py, or hand-authored) to resume mid-season. Mutually exclusive with --draft.",
    )
    parser.add_argument(
        "--wildcard-gw",
        type=int,
        default=None,
        help="Real gameweek number (e.g. 8) where the Wildcard chip is played: waives hits and lets transfers roll over as if none were made that week.",
    )

    args = parser.parse_args()

    if args.draft:
        print("Mode: pre-season draft.")
        resumed_team_state = None
    else:
        from pathlib import Path

        team_state_path = Path(args.team_state_json)
        if not team_state_path.exists():
            parser.error(
                f"'{team_state_path}' not found. Run scripts/fetch_team_state.py first, "
                "pass --team-state-json <path>, or use --draft for a pre-season draft."
            )
        print(f"Mode: mid-season from '{team_state_path}'.")
        resumed_team_state = TeamState.model_validate_json(team_state_path.read_text())

    solve_fpl_ilp(
        matrix_csv=args.matrix,
        starting_bank=args.bank,
        horizon_length=args.horizon,
        team_state=resumed_team_state,
        time_limit=args.time_limit,
        wildcard_gw=args.wildcard_gw,
    )
