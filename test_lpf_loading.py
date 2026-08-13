"""Pruebas de la frontera pura de preparación de cargas (`lpf_loading`)."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lpf_clubs import canon_base  # noqa: E402
from lpf_data_2026 import LPF_FIXTURE, ZONA_A_LPF_2026, ZONA_B_LPF_2026  # noqa: E402
from lpf_loading import (  # noqa: E402
    normalize_results_for_zones,
    prepare_automatic_update,
    prepare_offline_load,
    results_text,
)
from lpf_parsers import parse_tabla_anual  # noqa: E402
from lpf_reconcile import _lpf_result_stats, _lpf_results_fit_zones  # noqa: E402


def _rosters():
    za = canon_base(parse_tabla_anual(ZONA_A_LPF_2026)[0])
    zb = canon_base(parse_tabla_anual(ZONA_B_LPF_2026)[0])
    return {"A": za, "B": zb}


def _results_through_round(last_round, seed=1):
    rng = random.Random(seed)
    return [
        (row["l"], row["v"], rng.randrange(5), rng.randrange(5))
        for row in LPF_FIXTURE
        if int(row["f"]) <= int(last_round)
    ]


def _zones_from_results(results):
    rosters = _rosters()
    stats = _lpf_result_stats(results)
    out = {}
    for label, roster in rosters.items():
        rows = {}
        for pos, team in enumerate(roster, 1):
            row = dict(stats.get(team) or {"pj": 0, "pts": 0, "gf": 0, "ga": 0, "dg": 0})
            row["source_pos"] = pos
            rows[team] = row
        out[label] = rows
    return out


def _opening_snapshot():
    teams = [team for base in _rosters().values() for team in base]
    return {
        team: {"pj": 16, "pts": 20 + (idx % 12), "gf": 18 + (idx % 9), "ga": 15 + (idx % 7), "dg": 0}
        for idx, team in enumerate(teams)
    }


def test_normalize_results_for_zones_canonicaliza_y_filtra():
    zones = _rosters()
    rows = [
        ("River", "Barracas Central", "2", "1"),
        ("Real Madrid", "Boca", 1, 0),
        ("Barracas Central", "River Plate", 1, 2),
    ]
    normalized = normalize_results_for_zones(zones, rows)
    # La segunda fila es ajena al torneo; la tercera identifica el mismo partido
    # oficial invertido y reemplaza el marcador anterior sin duplicarlo.
    assert normalized == [("River Plate", "Barracas Central", 2, 1)]


def test_results_text_mantiene_formato_manual():
    assert results_text([("River Plate", "Boca Juniors", 2, 0)]) == "River Plate 2-0 Boca Juniors"


def test_prepare_offline_load_reconstruye_foto_completa():
    played = _results_through_round(2, seed=10)
    zones = _zones_from_results(played)
    prepared = prepare_offline_load(
        zones,
        previous_played=played[:15],
        builtin_played=played,
    )
    assert prepared["zones"] == zones
    assert _lpf_results_fit_zones(prepared["zones"], prepared["played"])
    assert len(prepared["played"]) == 30
    assert prepared["results_text"].count("\n") == 29


def test_prepare_automatic_update_acepta_fuentes_ya_normalizadas():
    played = _results_through_round(2, seed=20)
    zones = _zones_from_results(played)
    prepared = prepare_automatic_update(
        zones,
        previous_played=played[:15],
        futbolargentino_played=played,
        espn_played=played,
    )
    assert prepared["zones"] == zones
    assert _lpf_results_fit_zones(zones, prepared["played"])
    assert prepared["reconcile_note"] == ""
    assert prepared["expected_results"] == 30


def test_prepare_automatic_update_avanza_standings_atrasado_y_anual():
    round1 = _results_through_round(1, seed=30)
    round2 = _results_through_round(2, seed=30)
    zones_behind = _zones_from_results(round1)
    opening = _opening_snapshot()
    # La DG del snapshot no interviene en la validez básica; la suma autoritativa
    # recalcula la foto anual desde sus acumulados y las zonas avanzadas.
    annual = {
        team: {**row, "source_pos": pos}
        for pos, (team, row) in enumerate(opening.items(), 1)
    }
    prepared = prepare_automatic_update(
        zones_behind,
        annual=annual,
        opening=opening,
        previous_played=round1,
        espn_played=round2,
    )
    assert prepared["reconcile_note"]
    assert _lpf_results_fit_zones(prepared["zones"], prepared["played"])
    assert len(prepared["played"]) == 30
    assert len(prepared["reconciled_annual"]) == 30


def test_prepare_automatic_update_no_inventa_si_faltan_dos_fechas():
    round1 = _results_through_round(1, seed=40)
    round3 = _results_through_round(3, seed=40)
    zones_round3 = _zones_from_results(round3)
    prepared = prepare_automatic_update(
        zones_round3,
        previous_played=round1,
    )
    assert prepared["played"] == []
    assert prepared["inferred_played"] == []
    assert prepared["diagnostic_notes"]
    assert "La tabla implica 45 partidos" in prepared["coverage_note"]
