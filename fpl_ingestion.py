import requests
import polars as pl
import concurrent.futures

def fetch_player_history(player_id, session):
    """Fetches a specific player's historical points from the 2025/26 season."""
    url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
    try:
        resp = session.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            for season in data.get("history_past", []):
                # Ensure this matches the string FPL uses for last season
                if season.get("season_name") == "2025/26":
                    return season.get("total_points", 0)
    except requests.RequestException:
        pass
    
    return 0

def main():
    base_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    print("Fetching current 2026/27 bootstrap-static data...")
    
    session = requests.Session()
    response = session.get(base_url).json()
    elements = response.get("elements", [])
    
    players = []
    for el in elements:
        players.append({
            "player_id": el["id"],
            "name": f'{el["first_name"]} {el["second_name"]}',
            "pos_id": el["element_type"], # 1=GK, 2=DEF, 3=MID, 4=FWD
            "club_id": el["team"],
            "cost": el["now_cost"]        # FPL stores price as Cost * 10 (e.g., 100 = £10.0m)
        })
        
    print(f"Extracted {len(players)} players. Fetching 2025/26 historical points...")
    
    # Fetch historical points concurrently for speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_player_history, p["player_id"], session): p 
            for p in players
        }
        
        for future in concurrent.futures.as_completed(futures):
            p = futures[future]
            try:
                p["points_last_season"] = future.result()
            except Exception:
                p["points_last_season"] = 0
                
    # Load into Polars DataFrame
    df = pl.DataFrame(players)
    
    # Save output for the solver
    output_file = "fpl_players_2026.csv"
    df.write_csv(output_file)
    print(f"Data ingestion complete. Saved to {output_file}")

if __name__ == "__main__":
    main()
