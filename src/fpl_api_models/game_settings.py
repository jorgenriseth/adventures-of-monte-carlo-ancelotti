from typing import Annotated, Any

from pydantic import BaseModel, Field


class GameSettings(BaseModel):
    """Global rule set, system parameters, league constraints, and UI presentation constants."""

    # League Rules & Head-to-Head Config
    league_join_private_max: Annotated[
        int,
        Field(
            description="Maximum number of private leagues an individual manager can join (typically 30)"
        ),
    ]
    league_join_public_max: Annotated[
        int,
        Field(
            description="Maximum number of public leagues an individual manager can join (typically 5)"
        ),
    ]
    league_max_size_public_classic: Annotated[
        int,
        Field(
            description="Player cap for auto-created public classic leagues (typically 20)"
        ),
    ]
    league_max_size_public_h2h: Annotated[
        int,
        Field(
            description="Player cap for auto-created public Head-to-Head leagues (typically 20)"
        ),
    ]
    league_max_size_private_h2h: Annotated[
        int,
        Field(
            description="Maximum team capacity allowed in private H2H leagues (typically 16)"
        ),
    ]
    league_max_ko_rounds_private_h2h: Annotated[
        int,
        Field(
            description="Maximum knockout rounds allowed in private H2H leagues (typically 3)"
        ),
    ]
    league_prefix_public: Annotated[
        str,
        Field(
            description="Default naming string prefix for public leagues (e.g., 'League')"
        ),
    ]
    league_points_h2h_win: Annotated[
        int, Field(description="Points awarded for H2H match win (typically 3)")
    ]
    league_points_h2h_lose: Annotated[
        int, Field(description="Points awarded for H2H match loss (typically 0)")
    ]
    league_points_h2h_draw: Annotated[
        int, Field(description="Points awarded for H2H match draw (typically 1)")
    ]
    league_ko_first_instead_of_random: Annotated[
        bool,
        Field(
            description="If True, H2H knockout tiebreakers use seed order; if False, use random draws"
        ),
    ]
    league_h2h_tiebreak_stats: Annotated[
        list[str],
        Field(
            description="Stat order used to break ties in H2H leagues (e.g., ['+goals_scored', '-goals_conceded'])"
        ),
    ]

    # FPL Cup & Rank Percentiles
    cup_start_event_id: Annotated[
        int | None,
        Field(
            default=None,
            description="Gameweek ID when the official FPL Cup tournament begins (populated once qualifying starts)",
        ),
    ]
    cup_stop_event_id: Annotated[
        int | None,
        Field(
            default=None,
            description="Gameweek ID when the official FPL Cup tournament ends",
        ),
    ]
    cup_qualifying_method: Annotated[
        str | None,
        Field(
            default=None,
            description="Method used to qualify for the FPL Cup (e.g., 'rank', 'score')",
        ),
    ]
    cup_type: Annotated[
        str | None,
        Field(default=None, description="Type of cup tournament (e.g., 'knockout')"),
    ]
    featured_entries: Annotated[
        list[Any],
        Field(
            default_factory=list,
            description="Array of featured manager account IDs highlighted by FPL administrators",
        ),
    ]
    percentile_ranks: Annotated[
        list[int],
        Field(
            description="Predefined percentile boundaries used for global rank distribution metrics (e.g., [1, 5, 10, ..., 95])"
        ),
    ]
    underdog_differential: Annotated[
        int,
        Field(
            description="Point threshold used in underdog scoring or differential calculations (typically 5)"
        ),
    ]

    # Squad & Transfer Engine Rules
    squad_squadplay: Annotated[
        int, Field(description="Number of starting players (typically 11)")
    ]
    squad_squadsize: Annotated[
        int, Field(description="Total number of players per squad (typically 15)")
    ]
    squad_special_min: Annotated[
        int | None,
        Field(
            default=None,
            description="Minimum required special players in squad (used in specific game modes, typically null)",
        ),
    ]
    squad_special_max: Annotated[
        int | None,
        Field(
            default=None,
            description="Maximum allowed special players in squad (used in specific game modes, typically null)",
        ),
    ]
    squad_team_limit: Annotated[
        int,
        Field(
            description="Maximum allowed players from a single Premier League team (typically 3)"
        ),
    ]
    squad_total_spend: Annotated[
        int,
        Field(
            description="Starting budget in tenths of a million (e.g., 1000 = £100.0m)"
        ),
    ]
    transfers_sell_on_fee: Annotated[
        float,
        Field(
            description="Profit tax rate (e.g., 0.5 means managers keep 50% of price gain upon selling)"
        ),
    ]
    element_sell_at_purchase_price: Annotated[
        bool,
        Field(
            description="If True, players sell at original purchase price; if False, use standard price profit logic"
        ),
    ]
    max_extra_free_transfers: Annotated[
        int,
        Field(
            description="Cap on saved free transfers above the base 1 (e.g., 4 allows up to 5 total saved transfers)"
        ),
    ]
    transfers_cap: Annotated[
        int,
        Field(
            description="Maximum number of transfers allowed in a single transaction request (typically 20)"
        ),
    ]

    # System & Display Constants
    ui_currency_multiplier: Annotated[
        int,
        Field(
            description="Conversion factor used by clients to scale integer values to currency floats (e.g., 10: player value 50 / 10 = £5.0m)"
        ),
    ]
    ui_use_special_shirts: Annotated[
        bool,
        Field(
            description="If True, enables display of special edition shirts in the UI (typically False)"
        ),
    ]
    ui_special_shirt_exclusions: Annotated[
        list[Any],
        Field(
            default_factory=list,
            description="Array of team IDs or conditions that exclude special shirt rendering",
        ),
    ]
    stats_form_days: Annotated[
        int,
        Field(
            description="Time window in days used in player form calculation algorithms (typically 30)"
        ),
    ]
    sys_vice_captain_enabled: Annotated[
        bool,
        Field(
            description="Master switch enabling automatic captain fallback points (typically True)"
        ),
    ]
    timezone: Annotated[
        str,
        Field(
            description="Canonical API timestamp reference timezone (typically 'UTC')"
        ),
    ]
