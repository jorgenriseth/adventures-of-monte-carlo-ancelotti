from typing import Annotated

from pydantic import BaseModel, Field


class Phase(BaseModel):
    """Season segment used for overall and monthly leaderboard windows."""

    id: Annotated[
        int,
        Field(
            description="Primary key for the phase entity. 1 is reserved for 'Overall'; 2+ represent chronological monthly phases"
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Display label for the phase, such as 'Overall' or a calendar month name"
        ),
    ]
    start_event: Annotated[
        int,
        Field(
            ge=1,
            le=38,
            description="First Gameweek ID included in this phase scoring window",
        ),
    ]
    stop_event: Annotated[
        int,
        Field(
            ge=1,
            le=38,
            description="Final Gameweek ID included in this phase scoring window",
        ),
    ]
    highest_score: Annotated[
        int | None,
        Field(
            default=None,
            description="Highest cumulative points scored globally within this phase window; null for future/unplayed phases",
        ),
    ]
