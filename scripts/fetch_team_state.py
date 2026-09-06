import argparse
import os
from pathlib import Path

from myfpl.fpl_auth import fetch_team_state

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch the current team state (bank, squad, free transfers) and save it to disk."
    )
    parser.add_argument(
        "--manager-id",
        type=int,
        default=os.environ.get("FPL_MANAGER_ID"),
        help="FPL manager ID to fetch. Defaults to the FPL_MANAGER_ID env var.",
    )
    parser.add_argument(
        "--login-method",
        choices=["interactive", "browser", "env"],
        default="browser",
        help="How to authenticate (default: browser).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="team_state.json",
        help="Path to save the fetched TeamState JSON (default: team_state.json).",
    )
    args = parser.parse_args()

    if not args.manager_id:
        parser.error("Specify --manager-id or set the FPL_MANAGER_ID env var.")

    team_state = fetch_team_state(args.manager_id, method=args.login_method)

    Path(args.output).write_text(team_state.model_dump_json(indent=2))
    print(f"Saved team state to '{args.output}'.")

    print(f"\nBank: £{team_state.bank / 10:.1f}m")
    print(f"Free transfers: {team_state.free_transfers}")
    print("\nSquad:")
    for member in team_state.squad:
        print(
            f"  {member.player_id:>4}  {member.web_name:<20} "
            f"bought £{member.purchase_price / 10:.1f}m -> sells £{member.selling_price / 10:.1f}m"
        )
