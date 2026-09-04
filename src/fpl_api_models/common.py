from typing import Annotated, Any

from pydantic import BaseModel, Field


class Overrides(BaseModel):
    rules: Annotated[
        dict[str, Any],
        Field(
            description="Modifies default squad-building and transfer constraints (e.g., waiving transfer penalties, adjusting squad budget rules)"
        ),
    ]
    scoring: Annotated[
        dict[str, Any],
        Field(
            description="Modifies default point calculation logic (e.g., custom multipliers for match events like goals or clean sheets)"
        ),
    ]
    element_types: Annotated[
        list[Any],
        Field(
            description="Target-specific overrides for player positions (1=GKP, 2=DEF, 3=MID, 4=FWD) modifying formation constraints or scoring rules"
        ),
    ]
    pick_multiplier: Annotated[
        int | float | None,
        Field(
            default=None,
            description="Overrides default multipliers for squad positions (1=starting XI, 2=captain, 0=bench). Triple Captain=3, Bench Boost sets bench to 1",
        ),
    ]
