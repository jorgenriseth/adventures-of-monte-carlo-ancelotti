from typing import Annotated

from pydantic import BaseModel, Field


class PlayerStat(BaseModel):
    """UI schema and translation mapping for player performance metrics.

    Corresponds to the `element_stats` array in the FPL bootstrap-static API endpoint.
    """

    label: Annotated[
        str,
        Field(
            description="Human-readable display label for frontend tables, filters, and player profiles (e.g., 'Minutes played', 'Expected Goals')"
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Internal database key/field name matching player stats in elements/players and live feeds (e.g., 'minutes', 'expected_goals')"
        ),
    ]
