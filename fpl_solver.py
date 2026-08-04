import polars as pl
import pulp


def main():
    print("Loading data...")
    # Load data using Polars
    df = pl.read_csv("fpl_players_2026.csv")

    # Convert Polars DataFrame to a list of dicts for quick dictionary comprehensions
    players_data = df.to_dicts()
    player_ids = [p["player_id"] for p in players_data]

    # Build lookups for the objective function and constraints
    cost = {p["player_id"]: p["cost"] for p in players_data}
    points = {p["player_id"]: p["points_last_season"] for p in players_data}
    pos = {p["player_id"]: p["pos_id"] for p in players_data}
    club = {p["player_id"]: p["club_id"] for p in players_data}
    name = {p["player_id"]: p["name"] for p in players_data}

    # 1. Initialize the Problem
    prob = pulp.LpProblem("FPL_Set_And_Forget_Team", pulp.LpMaximize)

    # 2. Decision Variables
    x = pulp.LpVariable.dicts("squad", player_ids, cat="Binary")  # 15-man squad
    y = pulp.LpVariable.dicts("starting", player_ids, cat="Binary")  # Starting 11
    c = pulp.LpVariable.dicts("captain", player_ids, cat="Binary")  # Captain

    # 3. Objective Function: Maximize starting points + captain bonus
    prob += pulp.lpSum([points[i] * y[i] + points[i] * c[i] for i in player_ids])

    # 4. Constraints
    # Budget (£100.0m max, scaled by 10)
    prob += pulp.lpSum([cost[i] * x[i] for i in player_ids]) <= 1000

    # Total squad size constraints
    prob += pulp.lpSum([x[i] for i in player_ids]) == 15
    prob += pulp.lpSum([y[i] for i in player_ids]) == 11
    prob += pulp.lpSum([c[i] for i in player_ids]) == 1

    # Hierarchical constraints
    for i in player_ids:
        prob += c[i] <= y[i]  # Captain must be in starting 11
        prob += y[i] <= x[i]  # Starting 11 must be in 15-man squad

    # Club limit: Max 3 players per club
    club_ids = set(club.values())
    for team_id in club_ids:
        prob += pulp.lpSum([x[i] for i in player_ids if club[i] == team_id]) <= 3

    # Positional constraints for 15-man squad
    prob += pulp.lpSum([x[i] for i in player_ids if pos[i] == 1]) == 2
    prob += pulp.lpSum([x[i] for i in player_ids if pos[i] == 2]) == 5
    prob += pulp.lpSum([x[i] for i in player_ids if pos[i] == 3]) == 5
    prob += pulp.lpSum([x[i] for i in player_ids if pos[i] == 4]) == 3

    # Positional constraints for Starting 11 (valid formations)
    prob += pulp.lpSum([y[i] for i in player_ids if pos[i] == 1]) == 1
    prob += pulp.lpSum([y[i] for i in player_ids if pos[i] == 2]) >= 3
    prob += pulp.lpSum([y[i] for i in player_ids if pos[i] == 4]) >= 1

    # 5. Solve using CBC
    print("Solving ILP...")
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # 6. Output the optimal team
    print(f"Status: {pulp.LpStatus[prob.status]}")
    print(f"Optimal Projected Points: {pulp.value(prob.objective)}\n")

    total_cost = sum([cost[i] for i in player_ids if x[i].varValue == 1])
    print(f"Total Squad Cost: £{total_cost / 10:.1f}m\n")

    print("--- STARTING 11 ---")
    bench = []
    pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

    for i in player_ids:
        if y[i].varValue == 1:
            role = "(CAPTAIN)" if c[i].varValue == 1 else ""
            print(
                f"[{pos_map[pos[i]]}] {name[i]} - {points[i]} pts - £{cost[i] / 10:.1f}m {role}"
            )
        elif x[i].varValue == 1:
            bench.append(i)

    print("\n--- BENCH ---")
    for i in bench:
        print(f"[{pos_map[pos[i]]}] {name[i]} - {points[i]} pts - £{cost[i] / 10:.1f}m")


if __name__ == "__main__":
    main()
