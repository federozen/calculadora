"""Regresiones de agenda real y alcance temporal de la Previa."""
from __future__ import annotations

from lpf_data_2026 import LPF_FIXTURE
from lpf_schedule import (
    build_schedule_map,
    current_round,
    format_datetime,
    next_team_match,
    ordered_team_matches,
    parse_datetime,
    resolve_scope_games,
)


def _round_matches(round_no):
    return [(row["l"], row["v"]) for row in LPF_FIXTURE if row["f"] == round_no]


def _team_match(team, round_no):
    return next(
        (row["l"], row["v"])
        for row in LPF_FIXTURE
        if row["f"] == round_no and team in (row["l"], row["v"])
    )


def test_schedule_map_respeta_prioridad_y_compatibilidad_legacy():
    match = _team_match("Boca Juniors", 2)
    other = _team_match("River Plate", 2)
    primary = {f"{match[0]}|||{match[1]}": "2026-08-10T18:00:00-03:00"}
    secondary = {match: "2026-08-10T21:00:00-03:00"}
    legacy = {other: "2026-08-11", match: "2026-08-09"}

    schedule = build_schedule_map(primary, secondary, legacy)

    assert schedule[match].hour == 21
    assert schedule[other].hour == 15
    assert schedule[other].date().isoformat() == "2026-08-11"


def test_current_round_separa_un_postergado_de_la_fecha_operativa():
    postponed = _round_matches(2)[0]
    pending = [postponed, *_round_matches(3), *_round_matches(4)]

    jornada, official, delayed = current_round(pending, LPF_FIXTURE)

    assert jornada == 3
    assert set(official) == set(_round_matches(3))
    assert delayed == [(postponed, 2)]


def test_ordered_team_matches_prioriza_programacion_real_sobre_numero_de_fecha():
    team = "Boca Juniors"
    round2 = _team_match(team, 2)
    round3 = _team_match(team, 3)
    pending = [round2, round3]
    schedule = build_schedule_map(
        {f"{round3[0]}|||{round3[1]}": "2026-08-12T18:00:00-03:00"},
        {},
        {},
    )

    ordered = ordered_team_matches(team, pending, LPF_FIXTURE, schedule)

    assert [row["match"] for row in ordered] == [round3, round2]
    assert next_team_match(team, pending, LPF_FIXTURE, schedule)["match"] == round3


def test_scope_next_team_day_incluye_otros_partidos_del_mismo_dia():
    team = "Boca Juniors"
    own = _team_match(team, 3)
    other = next(match for match in _round_matches(3) if team not in match)
    pending = _round_matches(3) + _round_matches(4)
    schedule = build_schedule_map(
        {
            f"{own[0]}|||{own[1]}": "2026-08-14T20:00:00-03:00",
            f"{other[0]}|||{other[1]}": "2026-08-14T18:00:00-03:00",
        },
        {},
        {},
    )

    result = resolve_scope_games(
        team,
        pending,
        LPF_FIXTURE,
        schedule,
        scope="next_team_day",
    )

    assert own in result["games"]
    assert other in result["games"]
    assert result["own_match"] == own
    assert "14 de agosto" in result["label"]


def test_scope_sin_agenda_usa_fecha_oficial_y_postergados():
    postponed = _round_matches(2)[0]
    team = postponed[0]
    pending = [postponed, *_round_matches(3), *_round_matches(4)]

    result = resolve_scope_games(
        team,
        pending,
        LPF_FIXTURE,
        {},
        scope="extended_window",
    )

    assert result["round"] == 3
    assert postponed in result["games"]
    assert "postergado" in result["label"]


def test_parse_y_formato_datetime_convierten_a_hora_argentina():
    parsed = parse_datetime("2026-08-14T23:30:00Z")

    assert parsed.isoformat() == "2026-08-14T20:30:00-03:00"
    assert format_datetime(parsed) == "viernes 14 de agosto a las 20.30"
