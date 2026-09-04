from typing import Annotated, Any

from pydantic import BaseModel, Field


class Team(BaseModel):
    """Static information, real-world standings, and Fixture Difficulty Ratings (FDR) for a Premier League club."""

    # Identifiers & Metadata
    id: Annotated[
        int,
        Field(
            ge=1,
            le=20,
            description="The season-specific relational key (1–20) mapped to player records (element.team)",
        ),
    ]
    code: Annotated[
        int,
        Field(
            description="Permanent, multi-season club identifier used across Premier League systems (e.g., Arsenal is always 3)"
        ),
    ]
    name: Annotated[
        str,
        Field(description="Full official team name (e.g., 'Arsenal', 'Aston Villa')"),
    ]
    short_name: Annotated[
        str,
        Field(
            description="Standard 3-letter abbreviation used in UI widgets and fixtures (e.g., 'ARS', 'AVL')"
        ),
    ]
    pulse_id: Annotated[
        int,
        Field(
            description="Official entity ID used by the Premier League's core content API (Pulse Live) for media and match syncing"
        ),
    ]
    team_division: Annotated[
        Any | None,
        Field(
            default=None,
            description="Legacy field preserved for schema compatibility (typically null)",
        ),
    ]
    link_url: Annotated[
        str,
        Field(
            default="",
            description="Legacy link URL field preserved for schema compatibility (typically empty string)",
        ),
    ]

    # Real-World League Table Tracking
    position: Annotated[
        int,
        Field(
            ge=1,
            le=20,
            description="Current standing in the real-world Premier League table (1–20)",
        ),
    ]
    played: Annotated[
        int,
        Field(
            ge=0,
            description="Record of matches played in the active Premier League season",
        ),
    ]
    win: Annotated[
        int,
        Field(
            ge=0,
            description="Record of matches won in the active Premier League season",
        ),
    ]
    draw: Annotated[
        int,
        Field(
            ge=0,
            description="Record of matches drawn in the active Premier League season",
        ),
    ]
    loss: Annotated[
        int,
        Field(
            ge=0,
            description="Record of matches lost in the active Premier League season",
        ),
    ]
    points: Annotated[
        int,
        Field(
            ge=0,
            description="Total Premier League table points accumulated",
        ),
    ]
    form: Annotated[
        str | None,
        Field(
            default=None,
            description="Recent team form index (often null in bootstrap-static)",
        ),
    ]
    unavailable: Annotated[
        bool,
        Field(
            default=False,
            description="System flag indicating whether a club is temporarily barred or unscheduled for upcoming fixtures",
        ),
    ]

    # Fixture Difficulty Rating (FDR) Metrics
    strength: Annotated[
        int | None,
        Field(
            default=None,
            description="Aggregate team difficulty index (legacy field, often null)",
        ),
    ]
    strength_overall_home: Annotated[
        int,
        Field(
            description="Primary difficulty rating for home fixtures (typically scaled 1–5) used to calculate opponent FDR",
        ),
    ]
    strength_overall_away: Annotated[
        int,
        Field(
            description="Primary difficulty rating for away fixtures (typically scaled 1–5) used to calculate opponent FDR",
        ),
    ]
    strength_attack_home: Annotated[
        int,
        Field(
            description="Attack strength component for home fixtures utilized for positional FDR adjustments",
        ),
    ]
    strength_attack_away: Annotated[
        int,
        Field(
            description="Attack strength component for away fixtures utilized for positional FDR adjustments",
        ),
    ]
    strength_defence_home: Annotated[
        int,
        Field(
            description="Defensive strength component for home fixtures utilized for positional FDR adjustments",
        ),
    ]
    strength_defence_away: Annotated[
        int,
        Field(
            description="Defensive strength component for away fixtures utilized for positional FDR adjustments",
        ),
    ]
