from typing import Annotated, Any

from pydantic import BaseModel, Field


class PriceChangeProjection(BaseModel):
    """Nightly price change forecast projection."""

    offset: Annotated[
        int,
        Field(
            description="Days ahead from current date (0 = tonight, 1 = tomorrow night, etc.)"
        ),
    ]
    projected_percent: Annotated[
        str,
        Field(
            description="Projected net transfer progress percentage toward price change threshold"
        ),
    ]
    likelihood: Annotated[
        int,
        Field(
            description="Integer confidence/likelihood score for the projected price change"
        ),
    ]


class Player(BaseModel):
    """Core player entity containing bio data, price trends, ownership, match performance, and rankings.

    Corresponds to elements in the FPL bootstrap-static API endpoint.
    """

    # Player Identification & Bio Data
    id: Annotated[
        int,
        Field(description="Unique internal primary key for the player (1–~600+)"),
    ]
    code: Annotated[
        int,
        Field(
            description="Permanent multi-season player ID used to fetch asset media like shirt/headshot photos"
        ),
    ]
    first_name: Annotated[str, Field(description="Player first name")]
    second_name: Annotated[str, Field(description="Player second name / surname")]
    web_name: Annotated[
        str,
        Field(
            description="Shortened display name used on pitch view widgets and team line-ups"
        ),
    ]
    known_name: Annotated[
        str,
        Field(
            description="Commonly known single name (e.g., 'Alisson', 'Richarlison'); empty string if none"
        ),
    ]
    photo: Annotated[
        str,
        Field(description="Image filename mapped to code (e.g., '154561.jpg')"),
    ]
    birth_date: Annotated[
        str | None,
        Field(default=None, description="Player date of birth (YYYY-MM-DD)"),
    ]
    region: Annotated[
        int | None,
        Field(default=None, description="Country/region code ID"),
    ]
    team_join_date: Annotated[
        str | None,
        Field(
            default=None,
            description="Official club sign-on date (YYYY-MM-DD)",
        ),
    ]
    has_temporary_code: Annotated[
        bool,
        Field(
            description="Flag indicating if the player has a temporary ID pending permanent registration"
        ),
    ]
    opta_code: Annotated[
        str,
        Field(
            description="Provider tracking key mapping to official Opta statistical database IDs"
        ),
    ]
    squad_number: Annotated[
        int | None,
        Field(
            default=None,
            description="Real-world shirt number (null if unassigned)",
        ),
    ]

    # Team & Position Mapping
    team: Annotated[
        int,
        Field(
            ge=1,
            le=20,
            description="Foreign key matching teams.id (1–20)",
        ),
    ]
    team_code: Annotated[
        int,
        Field(
            description="Foreign key matching permanent teams.code",
        ),
    ]
    element_type: Annotated[
        int,
        Field(
            ge=1,
            le=4,
            description="Position classification (1 = GKP, 2 = DEF, 3 = MID, 4 = FWD)",
        ),
    ]

    # Availability, Health & Status Flags
    can_transact: Annotated[
        bool,
        Field(
            description="Toggles whether the player is available for transfer purchases"
        ),
    ]
    can_select: Annotated[
        bool,
        Field(
            description="Toggles whether the player is available for lineup selection"
        ),
    ]
    status: Annotated[
        str,
        Field(
            description="Availability code: 'a'=available, 'd'=doubtful, 'i'=injured, 's'=suspended, 'u'=unavailable, 'n'=not available"
        ),
    ]
    chance_of_playing_this_round: Annotated[
        int | None,
        Field(
            default=None,
            description="Likelihood percentage (0, 25, 50, 75, 100) of playing in current Gameweek (null = 100% fit)",
        ),
    ]
    chance_of_playing_next_round: Annotated[
        int | None,
        Field(
            default=None,
            description="Likelihood percentage (0, 25, 50, 75, 100) of playing in next Gameweek (null = 100% fit)",
        ),
    ]
    news: Annotated[
        str,
        Field(description="Official injury/suspension news text provided by FPL"),
    ]
    news_added: Annotated[
        str | None,
        Field(
            default=None,
            description="ISO timestamp when news was last updated/published",
        ),
    ]
    removed: Annotated[
        bool,
        Field(
            description="Flag indicating whether the player has left the Premier League or been removed from the game"
        ),
    ]
    special: Annotated[
        bool,
        Field(description="Internal flag for special promotional player entries"),
    ]
    scout_risks: Annotated[
        list[Any],
        Field(
            default_factory=list,
            description="Editorial notes regarding injury, rotation, or tactical risks",
        ),
    ]
    scout_news_link: Annotated[
        str,
        Field(
            default="",
            description="Link to editorial news article regarding player status",
        ),
    ]

    # Price Mechanics & Real-Time Fluctuations
    now_cost: Annotated[
        int,
        Field(
            description="Current player price in tenths of a million (e.g., 60 = £6.0m)"
        ),
    ]
    cost_change_event: Annotated[
        int,
        Field(
            description="Net price change during the current Gameweek in tenths of a million"
        ),
    ]
    cost_change_event_fall: Annotated[
        int,
        Field(
            description="Net price fall during the current Gameweek in tenths of a million"
        ),
    ]
    cost_change_start: Annotated[
        int,
        Field(
            description="Cumulative price change since season start in tenths of a million"
        ),
    ]
    cost_change_start_fall: Annotated[
        int,
        Field(
            description="Cumulative price fall since season start in tenths of a million"
        ),
    ]
    price_change_percent: Annotated[
        str,
        Field(
            description="Progress percentage toward the net transfer threshold required for a price change"
        ),
    ]
    price_change_hourly_rate: Annotated[
        int,
        Field(description="Net transfer velocity per hour"),
    ]
    price_change_projections: Annotated[
        list[PriceChangeProjection],
        Field(
            default_factory=list,
            description="Forecast array with projected net transfer percentage and likelihood for upcoming updates",
        ),
    ]
    price_change_locked_until: Annotated[
        str | None,
        Field(
            default=None,
            description="Date lock preventing price changes (e.g., following long injuries or transfers)",
        ),
    ]
    price_change_calibrating: Annotated[
        bool,
        Field(
            description="Server state flag indicating active price algorithm recalculation"
        ),
    ]

    # FPL Performance, Ownership & Market Metrics
    total_points: Annotated[
        int, Field(description="Total fantasy points accumulated across the season")
    ]
    event_points: Annotated[
        int, Field(description="Fantasy points scored in the current active Gameweek")
    ]
    points_per_game: Annotated[
        str,
        Field(description="Average fantasy points scored per appearance"),
    ]
    form: Annotated[
        str,
        Field(
            description="Weighted rolling average points over recent Gameweeks (typically 30 days)"
        ),
    ]
    ep_this: Annotated[
        str,
        Field(
            description="Expected Points projected by FPL algorithm for current Gameweek"
        ),
    ]
    ep_next: Annotated[
        str,
        Field(
            description="Expected Points projected by FPL algorithm for next Gameweek"
        ),
    ]
    selected_by_percent: Annotated[
        str,
        Field(
            description="Overall ownership percentage across all active FPL managers"
        ),
    ]
    in_dreamteam: Annotated[
        bool,
        Field(
            description="True if player is in the Dream Team for the current Gameweek"
        ),
    ]
    dreamteam_count: Annotated[
        int,
        Field(
            description="Total number of times selected in the Dream Team this season"
        ),
    ]
    value_form: Annotated[
        str,
        Field(description="Form-to-cost value ratio (form / now_cost)"),
    ]
    value_season: Annotated[
        str,
        Field(description="Points-to-cost value ratio (total_points / now_cost)"),
    ]
    transfers_in: Annotated[
        int,
        Field(description="Cumulative transfers in across the entire season"),
    ]
    transfers_in_event: Annotated[
        int,
        Field(description="Transfers in during the current Gameweek transfer window"),
    ]
    transfers_out: Annotated[
        int,
        Field(description="Cumulative transfers out across the entire season"),
    ]
    transfers_out_event: Annotated[
        int,
        Field(description="Transfers out during the current Gameweek transfer window"),
    ]

    # On-Pitch Match Statistics & Advanced Metrics
    minutes: Annotated[
        int, Field(description="Total minutes played in the Premier League this season")
    ]
    starts: Annotated[
        int, Field(description="Total starts in the starting XI this season")
    ]
    goals_scored: Annotated[
        int, Field(description="Total goals scored in the Premier League this season")
    ]
    assists: Annotated[int, Field(description="Total assists registered this season")]
    clean_sheets: Annotated[
        int, Field(description="Total clean sheets kept this season")
    ]
    goals_conceded: Annotated[
        int, Field(description="Total goals conceded while on the pitch")
    ]
    own_goals: Annotated[int, Field(description="Total own goals scored this season")]
    penalties_saved: Annotated[
        int, Field(description="Total penalty kicks saved by goalkeeper")
    ]
    penalties_missed: Annotated[
        int, Field(description="Total penalty kicks missed by penalty taker")
    ]
    yellow_cards: Annotated[
        int, Field(description="Total yellow cards received this season")
    ]
    red_cards: Annotated[int, Field(description="Total red cards received this season")]
    saves: Annotated[
        int, Field(description="Total saves made by goalkeeper this season")
    ]
    bonus: Annotated[
        int, Field(description="Cumulative bonus points awarded this season")
    ]
    bps: Annotated[
        int,
        Field(description="Raw underlying Bonus Points System cumulative score"),
    ]
    influence: Annotated[
        str,
        Field(
            description="ICT Index Influence metric measuring impact on match outcome"
        ),
    ]
    creativity: Annotated[
        str,
        Field(
            description="ICT Index Creativity metric measuring chance creation frequency"
        ),
    ]
    threat: Annotated[
        str,
        Field(description="ICT Index Threat metric measuring goal threat capability"),
    ]
    ict_index: Annotated[
        str,
        Field(description="ICT Index composite overall score"),
    ]
    clearances_blocks_interceptions: Annotated[
        int,
        Field(description="Cumulative clearances, blocks, and interceptions count"),
    ]
    recoveries: Annotated[int, Field(description="Cumulative ball recoveries count")]
    tackles: Annotated[int, Field(description="Cumulative successful tackles count")]
    defensive_contribution: Annotated[
        int,
        Field(description="Defensive contribution bonus events accumulated"),
    ]
    expected_goals: Annotated[
        str,
        Field(description="Total Expected Goals (xG) accumulated this season"),
    ]
    expected_assists: Annotated[
        str,
        Field(description="Total Expected Assists (xA) accumulated this season"),
    ]
    expected_goal_involvements: Annotated[
        str,
        Field(
            description="Total Expected Goal Involvements (xGI) accumulated this season"
        ),
    ]
    expected_goals_conceded: Annotated[
        str,
        Field(
            description="Total Expected Goals Conceded (xGC) while on pitch this season"
        ),
    ]

    # Normalized Per-90 Statistics
    expected_goals_per_90: Annotated[
        float,
        Field(description="Expected Goals normalized per 90 minutes played"),
    ]
    expected_assists_per_90: Annotated[
        float,
        Field(description="Expected Assists normalized per 90 minutes played"),
    ]
    expected_goal_involvements_per_90: Annotated[
        float,
        Field(
            description="Expected Goal Involvements normalized per 90 minutes played"
        ),
    ]
    expected_goals_conceded_per_90: Annotated[
        float,
        Field(description="Expected Goals Conceded normalized per 90 minutes played"),
    ]
    goals_conceded_per_90: Annotated[
        float,
        Field(description="Actual Goals Conceded normalized per 90 minutes played"),
    ]
    saves_per_90: Annotated[
        float,
        Field(description="Goalkeeper saves normalized per 90 minutes played"),
    ]
    clean_sheets_per_90: Annotated[
        float,
        Field(description="Clean sheets normalized per 90 minutes played"),
    ]
    defensive_contribution_per_90: Annotated[
        float,
        Field(
            description="Defensive contribution bonus rate normalized per 90 minutes played"
        ),
    ]
    starts_per_90: Annotated[
        float,
        Field(description="Match starts normalized per 90 minutes played"),
    ]

    # Set Piece Duties
    corners_and_indirect_freekicks_order: Annotated[
        int | None,
        Field(
            default=None,
            description="Priority rank for taking corners and indirect free kicks (1 = primary)",
        ),
    ]
    corners_and_indirect_freekicks_text: Annotated[
        str,
        Field(
            default="",
            description="Editorial notes regarding corner and indirect free kick taking duties",
        ),
    ]
    direct_freekicks_order: Annotated[
        int | None,
        Field(
            default=None,
            description="Priority rank for taking direct free kicks (1 = primary)",
        ),
    ]
    direct_freekicks_text: Annotated[
        str,
        Field(
            default="",
            description="Editorial notes regarding direct free kick taking duties",
        ),
    ]
    penalties_order: Annotated[
        int | None,
        Field(
            default=None,
            description="Priority rank for taking penalty kicks (1 = primary)",
        ),
    ]
    penalties_text: Annotated[
        str,
        Field(
            default="",
            description="Editorial notes regarding penalty kick taking duties",
        ),
    ]

    # Rankings (Global vs Positional)
    influence_rank: Annotated[
        int, Field(description="Global rank across all players by Influence metric")
    ]
    influence_rank_type: Annotated[
        int,
        Field(
            description="Positional rank within player's element_type by Influence metric"
        ),
    ]
    creativity_rank: Annotated[
        int, Field(description="Global rank across all players by Creativity metric")
    ]
    creativity_rank_type: Annotated[
        int,
        Field(
            description="Positional rank within player's element_type by Creativity metric"
        ),
    ]
    threat_rank: Annotated[
        int, Field(description="Global rank across all players by Threat metric")
    ]
    threat_rank_type: Annotated[
        int,
        Field(
            description="Positional rank within player's element_type by Threat metric"
        ),
    ]
    ict_index_rank: Annotated[
        int, Field(description="Global rank across all players by ICT Index score")
    ]
    ict_index_rank_type: Annotated[
        int,
        Field(
            description="Positional rank within player's element_type by ICT Index score"
        ),
    ]
    now_cost_rank: Annotated[
        int, Field(description="Global rank across all players by player price")
    ]
    now_cost_rank_type: Annotated[
        int,
        Field(
            description="Positional rank within player's element_type by player price"
        ),
    ]
    form_rank: Annotated[
        int, Field(description="Global rank across all players by current form")
    ]
    form_rank_type: Annotated[
        int,
        Field(
            description="Positional rank within player's element_type by current form"
        ),
    ]
    points_per_game_rank: Annotated[
        int,
        Field(description="Global rank across all players by points per game average"),
    ]
    points_per_game_rank_type: Annotated[
        int,
        Field(
            description="Positional rank within player's element_type by points per game"
        ),
    ]
    selected_rank: Annotated[
        int,
        Field(description="Global rank across all players by ownership percentage"),
    ]
    selected_rank_type: Annotated[
        int,
        Field(
            description="Positional rank within player's element_type by ownership percentage"
        ),
    ]


# Alias for backward compatibility / direct API terminology
Element = Player
