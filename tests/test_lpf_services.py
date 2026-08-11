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
