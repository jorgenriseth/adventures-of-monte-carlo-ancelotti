import logging
from collections.abc import Iterable

import polars as pl

from fpl_db.enums import Position
from fpl_db.models import Player, PlayerIDMap

from myfpl.constants import DATA_DIR

logger = logging.getLogger(__name__)

PLAYER_KEYS = (
    "code",
    "web_name",
    "first_name",
    "second_name",
    "element_type",
    "season",
    "team",
    "team_code",
    "id",
)
_VALID_POSITIONS = [p.value for p in Position]


def _players_raw_path(season: str) -> str:
    return f"{DATA_DIR}/players_raw_{season}.csv"


def load_players_raw(seasons: Iterable[str]) -> pl.DataFrame:
    frames = [
        pl.read_csv(_players_raw_path(season), null_values=("None",))
        .with_columns(pl.lit(season).alias("season"))
        .select(list(PLAYER_KEYS))
        for season in seasons
    ]
    return pl.concat(frames, how="diagonal_relaxed")


def to_players(df: pl.DataFrame) -> tuple[list[Player], list[PlayerIDMap]]:
    """Convert raw player rows into ORM instances, one Player per code (latest season wins) plus all id-maps."""
    valid = df.filter(pl.col("element_type").is_in(_VALID_POSITIONS))
    skipped = df.height - valid.height
    if skipped:
        # e.g. the "Manager" element_type introduced in later seasons, not yet modelled by Position
        logger.warning("Skipping %d player rows with unsupported element_type", skipped)

    id_maps = [
        PlayerIDMap(
            season=row["season"], player_code=row["code"], fpl_player_id=row["id"]
        )
        for row in valid.iter_rows(named=True)
    ]

    latest = (
        valid.sort("season")
        .group_by("code", maintain_order=True)
        .agg(
            pl.col("web_name").last(),
            pl.col("first_name").last(),
            pl.col("second_name").last(),
            pl.col("element_type").last(),
        )
    )
    players = [
        Player(
            code=row["code"],
            web_name=row["web_name"],
            full_name=f"{row['first_name']} {row['second_name']}".strip(),
            position=Position(row["element_type"]),
        )
        for row in latest.iter_rows(named=True)
    ]
    return players, id_maps
