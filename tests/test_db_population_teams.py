import polars as pl

from fpl_db.models import Team, TeamIDMap
from myfpl.db_population.teams import to_teams


def test_to_teams_dedupes_by_code_latest_season_wins():
    df = pl.DataFrame(
        {
            "season": ["2016-17", "2017-18", "2016-17"],
            "fpl_team_id": [1, 1, 5],
            "team_code": [3, 3, 7],
            "team_name": ["Arsenal", "Arsenal FC", "Aston Villa"],
        }
    )

    teams, id_maps = to_teams(df)

    assert {(t.code, t.name) for t in teams} == {(3, "Arsenal FC"), (7, "Aston Villa")}
    assert all(isinstance(t, Team) for t in teams)


def test_to_teams_produces_one_id_map_row_per_season():
    df = pl.DataFrame(
        {
            "season": ["2016-17", "2017-18"],
            "fpl_team_id": [1, 2],
            "team_code": [3, 3],
            "team_name": ["Arsenal", "Arsenal"],
        }
    )

    _, id_maps = to_teams(df)

    assert len(id_maps) == 2
    assert all(isinstance(m, TeamIDMap) for m in id_maps)
    assert {(m.season, m.team_code, m.fpl_team_id) for m in id_maps} == {
        ("2016-17", 3, 1),
        ("2017-18", 3, 2),
    }
