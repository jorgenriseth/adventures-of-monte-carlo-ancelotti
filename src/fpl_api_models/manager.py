from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class MyTeamPick(BaseModel):
    """A single squad player entry from the authenticated /api/my-team/{manager_id}/ endpoint."""

    element: Annotated[int, Field(description="Player ID (matches players.Player.id)")]
    position: Annotated[
        int,
        Field(
            ge=1,
            le=15,
            description="Squad slot order: 1-11 starting XI, 12-15 bench",
        ),
    ]
    multiplier: Annotated[
        int,
        Field(
            description="Scoring multiplier: 0 benched, 1 starting, 2 captain, 3 triple-captain"
        ),
    ]
    is_captain: Annotated[
        bool, Field(description="Whether this player is the current captain")
    ]
    is_vice_captain: Annotated[
        bool, Field(description="Whether this player is the current vice-captain")
    ]
    purchase_price: Annotated[
        int,
        Field(
            description="Price originally paid for this player, in tenths of a million"
        ),
    ]
    selling_price: Annotated[
        int,
        Field(
            description="Price the manager would receive if selling this player now, in tenths of a million"
        ),
    ]


class MyTeamTransfers(BaseModel):
    """Bank/transfer state from the 'transfers' section of the /api/my-team/ response.

    'limit' is this gameweek's transfer quota and does NOT decrease as transfers
    are made; 'made' tracks how many have already been confirmed this gameweek.
    Free transfers remaining = limit - made. 'limit' is null when a wildcard or
    free-hit chip is active this gameweek (transfers are unlimited/free).
    """

    model_config = ConfigDict(extra="allow")

    bank: Annotated[
        int,
        Field(
            description="Money in the bank not spent on the squad, in tenths of a million"
        ),
    ]
    limit: Annotated[
        int | None,
        Field(
            description="This gameweek's transfer quota, or null if unlimited (wildcard/free hit active)"
        ),
    ]
    made: Annotated[int, Field(description="Transfers already confirmed this gameweek")]


class MyTeam(BaseModel):
    """Full response from the authenticated /api/my-team/{manager_id}/ endpoint."""

    picks: Annotated[
        list[MyTeamPick], Field(description="The manager's current 15-man squad")
    ]
    transfers: Annotated[
        MyTeamTransfers, Field(description="Bank balance and free-transfer state")
    ]
    chips: Annotated[
        list[dict[str, Any]],
        Field(
            default_factory=list,
            description="Raw chip availability/usage entries, unvalidated",
        ),
    ]
