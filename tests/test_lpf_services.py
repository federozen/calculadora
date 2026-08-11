import json
from dataclasses import asdict

import pytest

from lpf_pisos import piso_por_corte
from lpf_scenarios import point_ladder, scenario_rank_bounds
from lpf_services import (
    CONTRACT_VERSION,
    ContractError,
    calculate_objective_floor,
    calculate_point_ladder,
    calculate_rank_window,
    calculate_standings,
)
from lpf_standings import DEFAULT_CRITERIOS, _orden
from lpf_version import __version__


def _assert_envelope(response, calculation):
    assert response["contract_version"] == CONTRACT_VERSION
    assert response["calculation_version"] == __version__
    assert response["calculation"] == calculation
    json.dumps(response, ensure_ascii=False)


def test_standings_service_matches_engine_exactly():
    teams = ["A", "B", "C", "D"]
    matches = [("A", "B", 2, 0), ("C", "D", 1, 1), ("A", "C", 0, 1)]
    response = calculate_standings({
        "teams": teams,
        "matches": [
            {"home": h, "away": a, "home_goals": gh, "away_goals": ga}
            for h, a, gh, ga in matches
        ],
    })
    _assert_envelope(response, "standings")
    order, stats = _orden(teams, matches, criterios=DEFAULT_CRITERIOS)
    assert response["result"]["positions"] == {team: i for i, team in enumerate(order, 1)}
    assert response["result"]["table"] == [
        {
            "position": i,
            "team": team,
            "played": stats[team]["pj"],
            "points": stats[team]["pts"],
            "goals_for": stats[team]["gf"],
            "goals_against": stats[team]["ga"],
            "goal_difference": stats[team]["dg"],
        }
        for i, team in enumerate(order, 1)
    ]


def test_standings_service_preserves_explicit_tiebreakers():
    response = calculate_standings({
        "teams": ["A", "B"],
        "matches": [{"home": "A", "away": "B", "home_goals": 0, "away_goals": 0}],
        "tiebreakers": [],
    })
    assert response["result"]["tiebreakers"] == []
    assert response["result"]["positions"] == {"A": 1, "B": 2}


def test_standings_service_rejects_unknown_team_cleanly():
    with pytest.raises(ContractError) as exc:
        calculate_standings({
            "teams": ["A", "B"],
            "matches": [{"home": "A", "away": "C", "home_goals": 1, "away_goals": 0}],
        })
    assert exc.value.code == "unknown_team"
    assert exc.value.field == "matches"
    json.dumps(exc.value.to_dict())


def test_point_ladder_service_matches_direct_engine():
    base = {"A": {"pts": 4}, "B": {"pts": 4}, "C": {"pts": 1}}
    matches = [("A", "B"), ("A", "C"), ("B", "C")]
    direct = point_ladder(base, matches, "A", 2)
    response = calculate_point_ladder({
        "base": base,
        "matches": [{"home": h, "away": a} for h, a in matches],
        "team": "A",
        "cutoff": 2,
    })
    _assert_envelope(response, "point_ladder")
    expected = dict(direct)
    expected["rows"] = [asdict(row) for row in direct["rows"]]
    assert response["result"] == expected


def test_rank_window_service_translates_json_fixed_results():
    base = {"A": 3, "B": 3, "C": 0}
    matches = [("A", "B"), ("A", "C")]
    fixed = {("A", "B"): "E"}
    direct = scenario_rank_bounds(base, matches, "A", fixed)
    response = calculate_rank_window({
        "base": base,
        "matches": [{"home": h, "away": a} for h, a in matches],
        "team": "A",
        "fixed": [{"home": "A", "away": "B", "result": "E"}],
    })
    _assert_envelope(response, "rank_window")
    expected = dict(direct)
    expected["by_points"] = [list(row) for row in direct["by_points"]]
    assert response["result"] == expected


def test_objective_floor_service_matches_direct_engine():
    base = {"A": 5, "B": 5, "C": 2, "D": 1}
    remaining = {"A": 1, "B": 1, "C": 1, "D": 1}
    matches = [("A", "B"), ("C", "D")]
    direct = piso_por_corte(base, remaining, matches, "A", 2, clave="playoffs", nombre="los playoffs")
    response = calculate_objective_floor({
        "base": base,
        "remaining": remaining,
        "matches": [{"home": h, "away": a} for h, a in matches],
        "team": "A",
        "cutoff": 2,
        "objective_key": "playoffs",
        "objective_name": "los playoffs",
    })
    _assert_envelope(response, "objective_floor")
    expected = asdict(direct)
    expected["caminos"] = [list(row) for row in expected["caminos"]]
    expected["minimum_possible"] = direct.minimo_posible
    expected["minimum_guarantee"] = direct.garantia_exacta
    expected["safe_total"] = direct.piso
    expected["exact_guarantee"] = direct.garantia_exacta
    expected["conservative_reference"] = direct.referencia_conservadora
    expected["safe_value"] = direct.piso
    expected["floor"] = direct.piso
    expected["reading"] = direct.lectura()
    assert response["result"] == expected


def test_service_modules_do_not_require_streamlit_or_http():
    import lpf_services

    source = open(lpf_services.__file__, encoding="utf-8").read()
    assert "import streamlit" not in source
    assert "import requests" not in source


def test_version_module_is_shared_with_audit_metadata():
    from lpf_models import AuditMetadata

    assert AuditMetadata().calculation_version == __version__


def _snapshot_fixture_payload():
    teams_a = ["Equipo A", "Equipo B", "Equipo C", "Equipo D"]
    teams_b = ["Equipo E", "Equipo F", "Equipo G", "Equipo H"]
    zones = {
        "A": {team: {"pts": 0, "pj": 0, "dg": 0, "gf": 0, "ga": 0} for team in teams_a},
        "B": {team: {"pts": 0, "pj": 0, "dg": 0, "gf": 0, "ga": 0} for team in teams_b},
    }
    fixture = [
        {"f": 1, "l": "Equipo A", "v": "Equipo B", "tipo": "zone", "zona": "A"},
        {"f": 1, "l": "Equipo C", "v": "Equipo D", "tipo": "zone", "zona": "A"},
        {"f": 1, "l": "Equipo E", "v": "Equipo F", "tipo": "zone", "zona": "B"},
        {"f": 1, "l": "Equipo G", "v": "Equipo H", "tipo": "zone", "zona": "B"},
    ]
    return {"zones": zones, "fixture": fixture}


def test_competition_snapshot_is_json_safe_and_keeps_pending_state():
    from lpf_services import prepare_competition_snapshot

    response = prepare_competition_snapshot(_snapshot_fixture_payload())
    _assert_envelope(response, "competition_snapshot")
    snapshot = response["result"]
    assert snapshot["remaining"] == {f"Equipo {letter}": 1 for letter in "ABCDEFGH"}
    assert snapshot["pending"][:2] == [
        {"home": "Equipo A", "away": "Equipo B"},
        {"home": "Equipo C", "away": "Equipo D"},
    ]
    assert snapshot["rules"] == {"annual_relegations": 1, "average_relegations": 1}
    assert snapshot["audit"]["level"] == "blocked"  # nómina sintética, pero la foto sigue siendo utilizable
    json.dumps(response, ensure_ascii=False)


def test_competition_batch_reuses_snapshot_for_multiple_exact_queries():
    from lpf_services import calculate_competition_batch, prepare_competition_snapshot

    snapshot = prepare_competition_snapshot(_snapshot_fixture_payload())["result"]
    response = calculate_competition_batch({
        "snapshot": snapshot,
        "queries": [
            {"id": "obj", "type": "objective_points", "scope": "zone", "zone": "A", "team": "Equipo A", "cutoff": 2},
            {"id": "ladder", "type": "point_ladder", "scope": "zone", "zone": "A", "team": "Equipo A", "cutoff": 2},
            {"id": "rank", "type": "rank_window", "scope": "zone", "zone": "A", "team": "Equipo A"},
        ],
    })
    _assert_envelope(response, "competition_batch")
    assert [row["id"] for row in response["result"]["queries"]] == ["obj", "ladder", "rank"]
    assert [row["type"] for row in response["result"]["queries"]] == [
        "objective_points", "point_ladder", "rank_window"
    ]
    json.dumps(response, ensure_ascii=False)


def test_competition_batch_objective_matches_direct_engine():
    from lpf_services import calculate_competition_batch, prepare_competition_snapshot

    snapshot = prepare_competition_snapshot(_snapshot_fixture_payload())["result"]
    base = snapshot["zones"]["A"]
    remaining = snapshot["remaining"]
    matches = [(row["home"], row["away"]) for row in snapshot["pending"] if row["home"] in base or row["away"] in base]
    direct = piso_por_corte(base, remaining, matches, "Equipo A", 2, clave="playoffs", nombre="los playoffs")
    response = calculate_competition_batch({
        "snapshot": snapshot,
        "queries": [{
            "type": "objective_points", "scope": "zone", "zone": "A", "team": "Equipo A", "cutoff": 2,
            "objective_key": "playoffs", "objective_name": "los playoffs",
        }],
    })
    result = response["result"]["queries"][0]["result"]
    assert result["minimum_possible"] == direct.minimo_posible
    assert result["minimum_guarantee"] == direct.garantia_exacta
    assert result["safe_total"] == direct.piso
    assert result["exact_guarantee"] == direct.garantia_exacta
    assert result["conservative_reference"] == direct.referencia_conservadora
    assert result["safe_value"] == direct.piso


def test_competition_batch_descent_combines_annual_and_average_history():
    from lpf_pisos import piso_no_descenso, promedio_totales
    from lpf_services import calculate_competition_batch

    annual = {team: {"pts": pts, "pj": 2} for team, pts in {"A": 2, "B": 3, "C": 4, "D": 5}.items()}
    zones = {"A": {team: {"pts": 0, "pj": 2} for team in annual}}
    previous = {team: {"points": pts, "played": 10} for team, pts in {"A": 10, "B": 13, "C": 16, "D": 19}.items()}
    snapshot = {
        "annual": annual,
        "zones": zones,
        "remaining": {team: 1 for team in annual},
        "pending": [{"home": "A", "away": "B"}, {"home": "C", "away": "D"}],
        "previous_averages": previous,
        "rules": {"annual_relegations": 1, "average_relegations": 1},
    }
    prom_totals = promedio_totales(annual, zones, previous)
    direct = piso_no_descenso(
        annual, snapshot["remaining"], [("A", "B"), ("C", "D")], "A",
        n_anual=1, prom_totales=prom_totals, n_prom=1,
    )
    response = calculate_competition_batch({
        "snapshot": snapshot,
        "queries": [{"type": "descent_points", "team": "A"}],
    })
    result = response["result"]["queries"][0]["result"]
    assert result["safe_value"] == direct.piso
    assert result["minimum_guarantee"] == direct.garantia_exacta
    assert result["safe_total"] == direct.piso
    assert result["exact_guarantee"] == direct.garantia_exacta
    assert result["conservative_reference"] == direct.referencia_conservadora


def test_snapshot_and_service_layers_do_not_import_streamlit_or_http():
    import lpf_snapshot

    source = open(lpf_snapshot.__file__, encoding="utf-8").read()
    assert "import streamlit" not in source
    assert "import requests" not in source


def test_competition_snapshot_real_fixture_keeps_30_teams_and_remaining_counts():
    from lpf_clubs import canon_base
    from lpf_data_2026 import LPF_FIXTURE, ZONA_A_LPF_2026, ZONA_B_LPF_2026
    from lpf_parsers import parse_tabla_anual
    from lpf_reconcile import _lpf_result_stats
    from lpf_services import prepare_competition_snapshot

    rosters = {
        "A": canon_base(parse_tabla_anual(ZONA_A_LPF_2026)[0]),
        "B": canon_base(parse_tabla_anual(ZONA_B_LPF_2026)[0]),
    }
    played = [
        (row["l"], row["v"], 1, 0)
        for row in LPF_FIXTURE
        if int(row["f"]) <= 2
    ]
    stats = _lpf_result_stats(played)
    zones = {
        label: {
            team: {**stats[team], "source_pos": pos}
            for pos, team in enumerate(roster, 1)
        }
        for label, roster in rosters.items()
    }
    response = prepare_competition_snapshot({
        "zones": zones,
        "played": [
            {"home": h, "away": a, "home_goals": gh, "away_goals": ga}
            for h, a, gh, ga in played
        ],
        "fixture": LPF_FIXTURE,
    })
    snapshot = response["result"]
    assert len(snapshot["teams"]) == 30
    assert set(snapshot["remaining"].values()) == {14}
    assert len(snapshot["pending"]) == 210
    json.dumps(response, ensure_ascii=False)


def test_service_floor_accessors_accept_legacy_piso_objetivo():
    from lpf_services import _floor_conservative_reference, _floor_exact_guarantee

    class LegacyFloor:
        def __init__(self, *, exacto, piso_exacto=None, piso_conservador=None):
            self.exacto = exacto
            self.piso_exacto = piso_exacto
            self.piso_conservador = piso_conservador

    exact = LegacyFloor(exacto=True, piso_exacto=25, piso_conservador=27)
    conservative = LegacyFloor(exacto=False, piso_exacto=None, piso_conservador=27)

    assert _floor_exact_guarantee(exact) == 25
    assert _floor_conservative_reference(exact) is None
    assert _floor_exact_guarantee(conservative) is None
    assert _floor_conservative_reference(conservative) == 27
