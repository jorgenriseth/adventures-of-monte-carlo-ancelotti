from collections.abc import Iterable

import polars as pl
from fpl_db.models import Team, TeamIDMap

from myfpl.constants import DATA_DIR

MASTER_TEAM_LIST_PATH = f"{DATA_DIR}/vastaav/data/master_team_list.csv"


def _teams_csv_path(season: str) -> str:
    return f"{DATA_DIR}/vastaav/data/{season}/teams.csv"


def _players_raw_path(season: str) -> str:
    return f"{DATA_DIR}/players_raw_{season}.csv"


def load_team_catalogue(seasons: Iterable[str]) -> pl.DataFrame:
    """Build a (season, fpl_team_id, team_code, team_name) table, one row per season/team."""
    master = pl.read_csv(MASTER_TEAM_LIST_PATH)

    frames = []
    for season in seasons:
        season_master = master.filter(pl.col("season") == season)
        if season_master.height > 0:
            # early seasons lack a per-season teams.csv - recover team_code via players_raw's (team, team_code) pairs
            codes = pl.read_csv(
                _players_raw_path(season), columns=["team", "team_code"]
            ).unique()
            frame = season_master.join(codes, on="team", how="inner").select(
                pl.lit(season).alias("season"),
                pl.col("team").alias("fpl_team_id"),
                pl.col("team_code"),
                pl.col("team_name"),
            )
        else:
            frame = pl.read_csv(
                _teams_csv_path(season), columns=["code", "id", "name"]
            ).select(
                pl.lit(season).alias("season"),
                pl.col("id").alias("fpl_team_id"),
                pl.col("code").alias("team_code"),
                pl.col("name").alias("team_name"),
            )
        frames.append(frame)
    return pl.concat(frames, how="diagonal_relaxed")


def to_teams(df: pl.DataFrame) -> tuple[list[Team], list[TeamIDMap]]:
    """Convert a team catalogue frame into ORM instances, one Team per code (latest season wins) plus all id-maps."""
    id_maps = [
        TeamIDMap(
            season=row["season"],
            team_code=row["team_code"],
            fpl_team_id=row["fpl_team_id"],
        )
        for row in df.iter_rows(named=True)
    ]

    latest = (
        df.sort("season")
        .group_by("team_code", maintain_order=True)
        .agg(pl.col("team_name").last())
    )
    teams = [
        Team(code=row["team_code"], name=row["team_name"])
        for row in latest.iter_rows(named=True)
    ]
    return teams, id_maps
