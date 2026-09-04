from typing import Annotated

from pydantic import BaseModel, Field

from fpl_api_models.common import Overrides


class GameWeek(BaseModel):
    id: Annotated[int, Field(description="Sequential Gameweek index (1 to 38)")]
    name: Annotated[str, Field(description="Display label (e.g., 'Gameweek 1')")]
    deadline_time: Annotated[
        str,
        Field(
            description="UTC ISO timestamp marking the exact cutoff for transfer and team selection locks"
        ),
    ]
    release_time: Annotated[
        str | None,
        Field(
            default=None,
            description="Server timestamp for when event configuration was pushed (None if pre-loaded)",
        ),
    ]
    average_entry_score: Annotated[
        int,
        Field(
            description="Mean points scored across all active managers (0 for unplayed Gameweeks)"
        ),
    ]
    finished: Annotated[
        bool,
        Field(description="True once all real-world fixtures in the Gameweek conclude"),
    ]
    data_checked: Annotated[
        bool,
        Field(
            description="True after processing pipeline finishes calculating bonus points, auto-substitutions, and rank shifts"
        ),
    ]
    highest_scoring_entry: Annotated[
        int, Field(description="Manager account ID who achieved the highest_score")
    ]
    deadline_time_epoch: Annotated[
        int,
        Field(
            description="Unix epoch timestamp (in seconds) corresponding to the deadline"
        ),
    ]
    deadline_time_game_offset: Annotated[
        int,
        Field(description="Server timing adjustment offset in seconds (typically 0)"),
    ]
    highest_score: Annotated[
        int,
        Field(
            description="Single highest Gameweek score achieved by any manager globally (None before play)"
        ),
    ]
    is_previous: Annotated[
        bool,
        Field(description="Boolean pointer tracking if this was the previous Gameweek"),
    ]
    is_current: Annotated[
        bool,
        Field(
            description="Boolean pointer tracking if this is the current active Gameweek"
        ),
    ]
    is_next: Annotated[
        bool,
        Field(
            description="Boolean pointer tracking if this is the next upcoming Gameweek"
        ),
    ]
    cup_leagues_created: Annotated[
        bool,
        Field(
            description="Tracks whether FPL Cup tournament brackets were generated for this Gameweek"
        ),
    ]
    h2h_ko_matches_created: Annotated[
        bool,
        Field(
            description="Tracks whether Head-to-Head league knockout rounds were generated"
        ),
    ]
    can_enter: Annotated[
        bool,
        Field(
            description="Indicates if a newly created manager account can begin playing from this Gameweek"
        ),
    ]
    can_manage: Annotated[
        bool,
        Field(
            description="Indicates if team edits, transfers, and chip selections are currently allowed"
        ),
    ]
    released: Annotated[
        bool,
        Field(
            description="Boolean indicating whether the Gameweek configuration is active in the published schedule"
        ),
    ]
    ranked_count: Annotated[
        int,
        Field(
            description="Total number of managers who received an official rank for this Gameweek"
        ),
    ]
    chip_plays: Annotated[
        list[dict[str, int]],
        Field(
            description="Array of objects detailing platform-wide chip counts (e.g., {'chip_name': 'bboost', 'num_played': 814606}). Empty for future Gameweeks"
        ),
    ]
    most_selected: Annotated[
        int, Field(description="Player ID owned by the largest percentage of managers")
    ]
    most_transferred_in: Annotated[
        int,
        Field(
            description="Player ID bought by the most managers during the transfer window"
        ),
    ]
    top_element: Annotated[
        int,
        Field(
            description="Player ID of the highest-scoring Premier League player of the Gameweek"
        ),
    ]
    top_element_info: Annotated[
        dict[str, int],
        Field(
            description="Key-value pair with the id and exact points scored by top_element"
        ),
    ]
    transfers_made: Annotated[
        int,
        Field(
            description="Total transfers executed across the entire platform leading into the deadline"
        ),
    ]
    most_captained: Annotated[
        int,
        Field(description="Player ID selected most frequently for the captain armband"),
    ]
    most_vice_captained: Annotated[
        int,
        Field(
            description="Player ID selected most frequently for the vice-captain armband"
        ),
    ]
    overrides: Annotated[
        Overrides,
        Field(
            description="Object container for temporary, Gameweek-specific rule or scoring changes (used for FPL Challenge modes)"
        ),
    ]
