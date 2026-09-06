from typing import Annotated

from pydantic import BaseModel, Field

from fpl_api_models.manager import MyTeam


class SquadMember(BaseModel):
    """A single owned player, with the buy/sell price split the solver needs."""

    player_id: Annotated[
        int, Field(description="Player ID (matches players.Player.id)")
    ]
    web_name: Annotated[
        str, Field(description="Display name, for eyeballing/editing the squad by hand")
    ]
    purchase_price: Annotated[
        int, Field(description="Price originally paid, in tenths of a million")
    ]
    selling_price: Annotated[
        int, Field(description="Price received if sold now, in tenths of a million")
    ]


class TeamState(BaseModel):
    """Solver-facing snapshot of a manager's mid-season position.

    Unlike the raw fpl_api_models mirrors, this is the shape optimize_fpl_squad.py
    consumes directly, regardless of whether it was populated via the authenticated
    my-team fetch or a hand-authored JSON fallback.
    """

    manager_id: Annotated[int, Field(description="FPL manager/entry ID")]
    bank: Annotated[int, Field(description="Cash in the bank, in tenths of a million")]
    free_transfers: Annotated[
        int,
        Field(
            ge=0,
            le=5,
            description="Free transfers available before incurring a point hit",
        ),
    ]
    squad: Annotated[list[SquadMember], Field(description="The current 15-man squad")]

    @classmethod
    def from_my_team(
        cls,
        manager_id: int,
        my_team: MyTeam,
        player_names: dict[int, str] | None = None,
    ) -> "TeamState":
        """Builds a TeamState from a parsed /api/my-team/ response.

        player_names (player_id -> web_name) is optional so a hand-authored
        TeamState JSON can still be loaded without it; falls back to the player_id
        itself as a string when a name isn't available.
        """
        player_names = player_names or {}
        limit = my_team.transfers.limit
        if limit is None:
            # Wildcard/free hit active this gameweek: transfers are unlimited, so the
            # free-transfer constraint doesn't bind. Report the schema's max as a stand-in.
            free_transfers = 5
        else:
            free_transfers = max(limit - my_team.transfers.made, 0)

        squad = [
            SquadMember(
                player_id=pick.element,
                web_name=player_names.get(pick.element, str(pick.element)),
                purchase_price=pick.purchase_price,
                selling_price=pick.selling_price,
            )
            for pick in my_team.picks
        ]
        return cls(
            manager_id=manager_id,
            bank=my_team.transfers.bank,
            free_transfers=free_transfers,
            squad=squad,
        )
