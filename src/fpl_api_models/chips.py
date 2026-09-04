from typing import Annotated

from pydantic import BaseModel, Field

from fpl_api_models.common import Overrides


class Chip(BaseModel):
    id: Annotated[
        int, Field(description="Unique database identifier for the chip object")
    ]
    name: Annotated[
        str,
        Field(
            description="Internal string identifier for the chip (e.g., 'wildcard', 'freehit', 'bboost', '3xc')"
        ),
    ]
    number: Annotated[
        int,
        Field(
            description="Instance ordinal of the chip for the season (e.g., Wildcard 1 vs Wildcard 2). Single-use chips default to 1"
        ),
    ]
    start_event: Annotated[
        int,
        Field(
            ge=1,
            le=38,
            description="First Gameweek ID in which this chip instance becomes playable",
        ),
    ]
    stop_event: Annotated[
        int,
        Field(
            ge=1,
            le=38,
            description="Final Gameweek ID in which this chip instance remains valid before expiring",
        ),
    ]
    chip_type: Annotated[
        str,
        Field(
            description="Functional engine category: 'transfer' (Wildcard, Free Hit) or 'team'/'scoring' (Bench Boost, Triple Captain)"
        ),
    ]
    overrides: Annotated[
        Overrides,
        Field(
            description="Dynamic rule modifications applied when this chip is active"
        ),
    ]
