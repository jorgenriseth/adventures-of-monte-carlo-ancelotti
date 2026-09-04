from typing import Annotated, Any

from pydantic import BaseModel, Field


class GameConfigSettings(BaseModel):
    """Configuration settings for game entry and content delivery."""

    entry_per_event: Annotated[
        bool,
        Field(
            description="If True, allows new entries per gameweek; if False, single season-long entry only"
        ),
    ]
    timezone: Annotated[
        str, Field(description="Timezone for all API timestamps (typically 'UTC')")
    ]
    static_content_url: Annotated[
        str,
        Field(
            description="Base URL for static assets like team badges and player photos"
        ),
    ]
    price_change_deadlines: Annotated[
        list[str],
        Field(
            description="Array of UTC ISO timestamps indicating when player price changes are processed"
        ),
    ]


class GameConfigRules(BaseModel):
    """Rule set for league constraints, squad building, and transfer mechanics.

    Note: This object duplicates parameters from game_settings, providing the same
    rule configurations within the game_config structure.
    """

    # League Rules & Head-to-Head Config
    league_join_private_max: Annotated[
        int,
        Field(
            description="Maximum number of private leagues an individual manager can join"
        ),
    ]
    league_join_public_max: Annotated[
        int,
        Field(
            description="Maximum number of public leagues an individual manager can join"
        ),
    ]
    league_max_size_public_classic: Annotated[
        int, Field(description="Player cap for auto-created public classic leagues")
    ]
    league_max_size_public_h2h: Annotated[
        int,
        Field(description="Player cap for auto-created public Head-to-Head leagues"),
    ]
    league_max_size_private_h2h: Annotated[
        int, Field(description="Maximum team capacity allowed in private H2H leagues")
    ]
    league_max_ko_rounds_private_h2h: Annotated[
        int, Field(description="Maximum knockout rounds allowed in private H2H leagues")
    ]
    league_prefix_public: Annotated[
        str, Field(description="Default naming string prefix for public leagues")
    ]
    league_points_h2h_win: Annotated[
        int, Field(description="Points awarded for H2H match win")
    ]
    league_points_h2h_lose: Annotated[
        int, Field(description="Points awarded for H2H match loss")
    ]
    league_points_h2h_draw: Annotated[
        int, Field(description="Points awarded for H2H match draw")
    ]
    league_ko_first_instead_of_random: Annotated[
        bool,
        Field(
            description="If True, H2H knockout tiebreakers use seed order; if False, use random draws"
        ),
    ]
    league_h2h_tiebreak_stats: Annotated[
        list[str], Field(description="Stat order used to break ties in H2H leagues")
    ]

    # Cup & Featured Entries
    cup_start_event_id: Annotated[
        int | None,
        Field(
            default=None,
            description="Gameweek ID when the official FPL Cup tournament begins",
        ),
    ]
    cup_stop_event_id: Annotated[
        int | None,
        Field(default=None, description="Gameweek ID when the FPL Cup tournament ends"),
    ]
    cup_qualifying_method: Annotated[
        str | None,
        Field(default=None, description="Method used to qualify for the FPL Cup"),
    ]
    cup_type: Annotated[
        str | None, Field(default=None, description="Type of cup tournament")
    ]
    featured_entries: Annotated[
        list[Any],
        Field(
            default_factory=list,
            description="Array of featured manager account IDs highlighted by administrators",
        ),
    ]
    percentile_ranks: Annotated[
        list[int],
        Field(
            description="Predefined percentile boundaries for global rank distribution metrics"
        ),
    ]
    underdog_differential: Annotated[
        int,
        Field(
            description="Point threshold used in underdog scoring or differential calculations"
        ),
    ]

    # Squad Building Rules
    squad_squadplay: Annotated[
        int, Field(description="Number of starting players in the active lineup")
    ]
    squad_squadsize: Annotated[
        int, Field(description="Total number of players per squad")
    ]
    squad_special_min: Annotated[
        int | None,
        Field(
            default=None,
            description="Minimum required special players in squad (used in specific game modes)",
        ),
    ]
    squad_special_max: Annotated[
        int | None,
        Field(
            default=None,
            description="Maximum allowed special players in squad (used in specific game modes)",
        ),
    ]
    squad_team_limit: Annotated[
        int,
        Field(
            description="Maximum allowed players from a single Premier League team in a squad"
        ),
    ]
    squad_total_spend: Annotated[
        int,
        Field(
            description="Starting budget in tenths of a million (e.g., 1000 = £100.0m)"
        ),
    ]

    # Transfer & Pricing Rules
    element_sell_at_purchase_price: Annotated[
        bool,
        Field(
            description="If True, players sell at original purchase price; if False, use standard price profit logic"
        ),
    ]
    transfers_sell_on_fee: Annotated[
        float,
        Field(
            description="Profit tax rate (e.g., 0.5 means managers keep 50% of price gain upon selling)"
        ),
    ]
    max_extra_free_transfers: Annotated[
        int,
        Field(
            description="Cap on saved free transfers above the base 1 free transfer per week"
        ),
    ]
    transfers_cap: Annotated[
        int,
        Field(
            description="Maximum number of transfers allowed in a single transaction request"
        ),
    ]

    # UI & System Constants
    ui_currency_multiplier: Annotated[
        int,
        Field(
            description="Conversion factor used by clients to scale integer values to currency floats"
        ),
    ]
    ui_use_special_shirts: Annotated[
        bool,
        Field(
            description="If True, enables display of special edition shirts in the UI"
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
            description="Time window in days used in player form calculation algorithms"
        ),
    ]
    sys_vice_captain_enabled: Annotated[
        bool,
        Field(description="Master switch enabling automatic captain fallback points"),
    ]


class PositionScoring(BaseModel):
    """Position-specific scoring values (GKP, DEF, MID, FWD)."""

    GKP: Annotated[int, Field(description="Points for Goalkeeper position")]
    DEF: Annotated[int, Field(description="Points for Defender position")]
    MID: Annotated[int, Field(description="Points for Midfielder position")]
    FWD: Annotated[int, Field(description="Points for Forward position")]


class GameConfigScoring(BaseModel):
    """Point allocation system for match events and player actions."""

    # Play Time Points
    long_play: Annotated[
        int, Field(description="Points for playing 60+ minutes (typically 2)")
    ]
    short_play: Annotated[
        int, Field(description="Points for playing 1-59 minutes (typically 1)")
    ]

    # Defensive Actions
    goals_conceded: Annotated[
        PositionScoring,
        Field(
            description="Points deducted per 2 goals conceded (position-specific: -1 per 2 for GKP/DEF, 0 for MID/FWD)"
        ),
    ]
    clean_sheets: Annotated[
        PositionScoring,
        Field(
            description="Points for keeping a clean sheet (position-specific, typically 4 for GKP/DEF, 1 for MID, 0 for FWD)"
        ),
    ]
    saves: Annotated[
        int,
        Field(
            description="Points awarded per 3 saves made by goalkeeper (typically 1)"
        ),
    ]
    defensive_contribution: Annotated[
        PositionScoring,
        Field(
            description="Bonus points (+2) awarded to outfield positions when meeting defensive action thresholds (tackles, blocks, interceptions, recoveries)"
        ),
    ]

    # Attacking Actions
    goals_scored: Annotated[
        PositionScoring,
        Field(
            description="Points per goal scored (position-specific, typically 10 for GKP, 6 for DEF, 5 for MID, 4 for FWD)"
        ),
    ]
    assists: Annotated[int, Field(description="Points per assist (typically 3)")]

    # Penalties & Cards
    penalties_saved: Annotated[
        int, Field(description="Points for saving a penalty (typically 5)")
    ]
    penalties_missed: Annotated[
        int, Field(description="Points deducted for missing a penalty (typically -2)")
    ]
    yellow_cards: Annotated[
        int, Field(description="Points deducted per yellow card (typically -1)")
    ]
    red_cards: Annotated[
        int, Field(description="Points deducted per red card (typically -3)")
    ]
    own_goals: Annotated[
        int, Field(description="Points deducted per own goal (typically -2)")
    ]

    # Bonus & Advanced Stats
    bonus: Annotated[
        int,
        Field(
            description="Points per bonus point awarded (1 point per bonus, max 3 bonus per match)"
        ),
    ]
    bps: Annotated[
        int,
        Field(
            description="Placeholder hook for Bonus Point System raw score (0 in standard mode; BPS used for bonus calculation only)"
        ),
    ]
    influence: Annotated[
        int,
        Field(description="Placeholder hook for Influence metric (0 in standard mode)"),
    ]
    creativity: Annotated[
        int,
        Field(
            description="Placeholder hook for Creativity metric (0 in standard mode)"
        ),
    ]
    threat: Annotated[
        int,
        Field(description="Placeholder hook for Threat metric (0 in standard mode)"),
    ]
    ict_index: Annotated[
        int,
        Field(
            description="Placeholder hook for ICT Index composite metric (0 in standard mode)"
        ),
    ]

    # Expected Stats (xG, xA, xGC)
    expected_goals: Annotated[
        int,
        Field(
            description="Placeholder hook for expected goals metric (0 in standard mode; available for alternative scoring formats)"
        ),
    ]
    expected_assists: Annotated[
        int,
        Field(
            description="Placeholder hook for expected assists metric (0 in standard mode; available for alternative scoring formats)"
        ),
    ]
    expected_goal_involvements: Annotated[
        int,
        Field(
            description="Placeholder hook for expected goal involvements (0 in standard mode; available for alternative scoring formats)"
        ),
    ]
    expected_goals_conceded: Annotated[
        int,
        Field(
            description="Placeholder hook for expected goals conceded (0 in standard mode; available for alternative scoring formats)"
        ),
    ]

    # Granular Stats
    tackles: Annotated[
        int,
        Field(
            description="Placeholder hook for points per tackle (0 in standard mode)"
        ),
    ]
    clearances_blocks_interceptions: Annotated[
        int,
        Field(
            description="Placeholder hook for clearances, blocks, and interceptions (0 in standard mode; used in defensive_contribution threshold logic)"
        ),
    ]
    recoveries: Annotated[
        int,
        Field(
            description="Placeholder hook for ball recoveries (0 in standard mode; used in defensive_contribution threshold logic)"
        ),
    ]
    starts: Annotated[
        int,
        Field(
            description="Placeholder hook for starting XI appearance bonus (0 in standard mode)"
        ),
    ]

    # Manager Mode Scoring (FPL Challenge & Alternative Formats)
    special_multiplier: Annotated[
        int,
        Field(
            description="Multiplier for special player category in FPL Challenge modes (1 in standard mode)"
        ),
    ]
    mng_goals_scored: Annotated[
        PositionScoring,
        Field(
            description="FPL Challenge: points for real-world manager's team goals scored (position-specific, 0 in standard mode)"
        ),
    ]
    mng_clean_sheets: Annotated[
        PositionScoring,
        Field(
            description="FPL Challenge: points for real-world manager's team clean sheet (position-specific, 0 in standard mode)"
        ),
    ]
    mng_win: Annotated[
        PositionScoring,
        Field(
            description="FPL Challenge: points for real-world manager's team match win (position-specific, 0 in standard mode)"
        ),
    ]
    mng_draw: Annotated[
        PositionScoring,
        Field(
            description="FPL Challenge: points for real-world manager's team match draw (position-specific, 0 in standard mode)"
        ),
    ]
    mng_loss: Annotated[
        int,
        Field(
            description="FPL Challenge: points for real-world manager's team match loss (0 in standard mode)"
        ),
    ]
    mng_underdog_win: Annotated[
        PositionScoring,
        Field(
            description="FPL Challenge: bonus points when real-world manager's underdog team wins (position-specific, 0 in standard mode)"
        ),
    ]
    mng_underdog_draw: Annotated[
        PositionScoring,
        Field(
            description="FPL Challenge: bonus points when real-world manager's underdog team draws (position-specific, 0 in standard mode)"
        ),
    ]


class GameConfig(BaseModel):
    """Complete game configuration including settings, rules, and scoring system."""

    settings: Annotated[
        GameConfigSettings,
        Field(description="Configuration settings for game entry and content delivery"),
    ]
    rules: Annotated[
        GameConfigRules,
        Field(
            description="Rule set for league constraints, squad building, and transfer mechanics"
        ),
    ]
    scoring: Annotated[
        GameConfigScoring,
        Field(
            description="Point allocation system for match events and player actions"
        ),
    ]
