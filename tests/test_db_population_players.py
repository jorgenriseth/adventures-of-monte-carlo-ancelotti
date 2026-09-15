import polars as pl

from fpl_db.enums import Position
from fpl_db.models import Player, PlayerIDMap
from myfpl.db_population.players import to_players


def _row(**overrides):
    row = {
        "code": 1,
        "web_name": "Salah",
        "first_name": "Mohamed",
        "second_name": "Salah",
        "element_type": 3,
        "season": "2016-17",
        "team": 9,
        "team_code": 14,
        "id": 101,
    }
    row.update(overrides)
    return row


def test_to_players_dedupes_by_code_latest_season_wins():
    df = pl.DataFrame(
        [
            _row(season="2016-17", web_name="Salah", element_type=3, id=101),
            _row(season="2017-18", web_name="M.Salah", element_type=4, id=201),
        ]
    )

    players, _ = to_players(df)

    assert len(players) == 1
    player = players[0]
    assert isinstance(player, Player)
    assert player.web_name == "M.Salah"
    assert player.full_name == "Mohamed Salah"
    assert player.position == Position.FWD


def test_to_players_produces_one_id_map_row_per_season():
    df = pl.DataFrame(
        [
            _row(season="2016-17", id=101),
            _row(season="2017-18", id=201),
        ]
    )

    _, id_maps = to_players(df)

    assert len(id_maps) == 2
    assert all(isinstance(m, PlayerIDMap) for m in id_maps)
    assert {(m.season, m.player_code, m.fpl_player_id) for m in id_maps} == {
        ("2016-17", 1, 101),
        ("2017-18", 1, 201),
    }


def test_to_players_skips_unsupported_element_type():
    df = pl.DataFrame(
        [
            _row(code=1, element_type=3),
            _row(code=2, element_type=5),  # e.g. unmodelled "Manager" position
        ]
    )

    players, id_maps = to_players(df)

    assert [p.code for p in players] == [1]
    assert [m.player_code for m in id_maps] == [1]
