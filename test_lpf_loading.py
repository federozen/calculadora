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


def test_prepare_automatic_update_reconcilia_49_a_61_con_fecha_siguiente_parcial():
    """Regresión del caso real: 49 resultados base, 61 implícitos en la tabla.

    La base ya contiene cuatro partidos de la Fecha 4. Luego se completa el resto de
    esa fecha y se juega Racing-Banfield de Fecha 5. Los feeds automáticos pueden
    venir vacíos: si PJ/puntos/GF/GC/DG + fixture fijan una única solución, la carga
    debe reconstruir exactamente los 12 marcadores faltantes.
    """
    rng = random.Random(3861)
    all_results = {
        (row["l"], row["v"]): (row["l"], row["v"], rng.randrange(4), rng.randrange(4))
        for row in LPF_FIXTURE
        if int(row["f"]) <= 5
    }
    through_round3 = [
        result for pair, result in all_results.items()
        if next(
            int(row["f"])
            for row in LPF_FIXTURE
            if (row["l"], row["v"]) == pair
        ) <= 3
    ]
    builtin_round4_pairs = {
        ("Rosario Central", "Aldosivi"),
        ("Independiente Rivadavia", "Estudiantes de Río Cuarto"),
        ("Deportivo Riestra", "Estudiantes de La Plata"),
        ("Atlético Tucumán", "Sarmiento"),
    }
    baseline = through_round3 + [all_results[pair] for pair in builtin_round4_pairs]
    round4 = [
        all_results[(row["l"], row["v"])]
        for row in LPF_FIXTURE
        if int(row["f"]) == 4
    ]
    first_round5 = all_results[("Racing", "Banfield")]
    full = [*through_round3, *round4, first_round5]
    zones = _zones_from_results(full)

    assert len(baseline) == 49
    assert len(full) == 61
    prepared = prepare_automatic_update(zones, builtin_played=baseline)

    assert len(prepared["inferred_played"]) == 12
    assert len(prepared["played"]) == 61
    assert _lpf_results_fit_zones(zones, prepared["played"])
    assert "Fechas 4-5" in prepared["inferred_note"]
    assert "conciliación determinística 12" in prepared["coverage_note"]


def test_prepare_automatic_update_reconcilia_49_a_67_sin_tope_fijo_de_partidos():
    """Regresión del caso real siguiente: 49 resultados base y 67 implícitos.

    Se completa la Fecha 4 y se juegan siete partidos de la Fecha 5. El respaldo
    determinístico debe intentar los 18 faltantes: la cantidad ya no se corta en 16.
    """
    rng = random.Random(3864)
    all_results = {
        (row["l"], row["v"]): (row["l"], row["v"], rng.randrange(4), rng.randrange(4))
        for row in LPF_FIXTURE
        if int(row["f"]) <= 5
    }
    through_round3 = [
        result for pair, result in all_results.items()
        if next(
            int(row["f"])
            for row in LPF_FIXTURE
            if (row["l"], row["v"]) == pair
        ) <= 3
    ]
    builtin_round4_pairs = {
        ("Rosario Central", "Aldosivi"),
        ("Independiente Rivadavia", "Estudiantes de Río Cuarto"),
        ("Deportivo Riestra", "Estudiantes de La Plata"),
        ("Atlético Tucumán", "Sarmiento"),
    }
    baseline = through_round3 + [all_results[pair] for pair in builtin_round4_pairs]
    round4 = [
        all_results[(row["l"], row["v"])]
        for row in LPF_FIXTURE
        if int(row["f"]) == 4
    ]
    round5 = [
        all_results[(row["l"], row["v"])]
        for row in LPF_FIXTURE
        if int(row["f"]) == 5
    ]
    full = [*through_round3, *round4, *round5[:7]]
    zones = _zones_from_results(full)

    assert len(baseline) == 49
    assert len(full) == 67
    prepared = prepare_automatic_update(zones, builtin_played=baseline)

    assert len(prepared["inferred_played"]) == 18
    assert len(prepared["played"]) == 67
    assert _lpf_results_fit_zones(zones, prepared["played"])
    assert "Fechas 4-5" in prepared["inferred_note"]
    assert "conciliación determinística 18" in prepared["coverage_note"]


def test_prepare_automatic_update_no_infiere_dos_fechas_si_hay_mas_de_una_solucion():
    round1 = _results_through_round(1, seed=3862)
    round3 = _results_through_round(3, seed=3862)
    zones_round3 = _zones_from_results(round3)
    prepared = prepare_automatic_update(zones_round3, previous_played=round1)
    assert prepared["played"] == []
    assert prepared["inferred_played"] == []
    assert "más de una" in prepared["inferred_note"]


def test_prepare_automatic_update_no_duplica_diagnostico_si_feeds_aportan_lo_mismo():
    """Dos feeds vacíos no deben repetir el mismo bloque de diferencias."""
    round1 = _results_through_round(1, seed=3863)
    round3 = _results_through_round(3, seed=3863)
    zones_round3 = _zones_from_results(round3)

    prepared = prepare_automatic_update(
        zones_round3,
        builtin_played=round1,
        futbolargentino_played=[],
        espn_played=[],
    )

    assert prepared["played"] == []
    assert len(prepared["diagnostic_notes"]) == 1
    assert prepared["diagnostic_notes"][0].startswith(
        "base validada + LPF oficial:"
    )


def test_prepare_automatic_update_prioriza_lpf_oficial_y_completa_foto():
    baseline = _results_through_round(3, seed=3900)
    official = _results_through_round(6, seed=3900)
    zones = _zones_from_results(official)

    prepared = prepare_automatic_update(
        zones,
        builtin_played=baseline,
        official_played=official,
        futbolargentino_played=[],
        espn_played=[],
    )

    assert len(prepared["played"]) == 90
    assert _lpf_results_fit_zones(zones, prepared["played"])
    assert "LPF oficial aportó 90" in prepared["coverage_note"]
    assert prepared["inferred_played"] == []


def test_prepare_automatic_update_reconstruye_49_a_87_con_lpf_oficial_explicita():
    """Caso real de agosto: 49 incluidos + resultados oficiales de Fechas 4-6."""
    rng = random.Random(3867)
    by_pair = {
        (row["l"], row["v"]): (row["l"], row["v"], rng.randrange(4), rng.randrange(4))
        for row in LPF_FIXTURE
        if int(row["f"]) <= 6
    }
    round3 = [
        by_pair[(row["l"], row["v"])]
        for row in LPF_FIXTURE if int(row["f"]) <= 3
    ]
    built_round4_pairs = {
        ("Rosario Central", "Aldosivi"),
        ("Independiente Rivadavia", "Estudiantes de Río Cuarto"),
        ("Deportivo Riestra", "Estudiantes de La Plata"),
        ("Atlético Tucumán", "Sarmiento"),
    }
    baseline = round3 + [by_pair[pair] for pair in built_round4_pairs]
    round4_5 = [
        by_pair[(row["l"], row["v"])]
        for row in LPF_FIXTURE if int(row["f"]) in {4, 5}
    ]
    round6 = [
        by_pair[(row["l"], row["v"])]
        for row in LPF_FIXTURE if int(row["f"]) == 6
    ]
    # La foto del lunes 24/8 tenía 12 de 15 partidos de la Fecha 6 finalizados.
    full = [*round3, *round4_5, *round6[:12]]
    official = [*round4_5, *round6[:12]]
    zones = _zones_from_results(full)

    assert len(baseline) == 49
    assert len(full) == 87
    prepared = prepare_automatic_update(
        zones,
        builtin_played=baseline,
        official_played=official,
        futbolargentino_played=[],
        espn_played=[],
    )

    assert len(prepared["played"]) == 87
    assert _lpf_results_fit_zones(zones, prepared["played"])
    assert prepared["inferred_played"] == []
    assert "LPF oficial aportó 42" in prepared["coverage_note"]


def test_prepare_automatic_update_reconstruye_49_a_90_al_cerrar_fecha6():
    """Regresión del caso real 25/8: la Fecha 6 ya terminó completa.

    La base incluida conserva 45 partidos de Fechas 1-3 + cuatro de Fecha 4. El
    hub oficial de las Fechas 4-6 puede aportar las 45 fichas explícitas de esas
    jornadas; cuatro se superponen con la base y la unión exacta debe cerrar en 90.
    """
    rng = random.Random(3868)
    by_pair = {
        (row["l"], row["v"]): (row["l"], row["v"], rng.randrange(4), rng.randrange(4))
        for row in LPF_FIXTURE if int(row["f"]) <= 6
    }
    round3 = [
        by_pair[(row["l"], row["v"])]
        for row in LPF_FIXTURE if int(row["f"]) <= 3
    ]
    built_round4_pairs = {
        ("Rosario Central", "Aldosivi"),
        ("Independiente Rivadavia", "Estudiantes de Río Cuarto"),
        ("Deportivo Riestra", "Estudiantes de La Plata"),
        ("Atlético Tucumán", "Sarmiento"),
    }
    baseline = round3 + [by_pair[pair] for pair in built_round4_pairs]
    official = [
        by_pair[(row["l"], row["v"])]
        for row in LPF_FIXTURE if int(row["f"]) in {4, 5, 6}
    ]
    full = [
        by_pair[(row["l"], row["v"])]
        for row in LPF_FIXTURE if int(row["f"]) <= 6
    ]
    zones = _zones_from_results(full)

    assert len(baseline) == 49
    assert len(official) == 45
    assert len(full) == 90
    prepared = prepare_automatic_update(
        zones,
        builtin_played=baseline,
        official_played=official,
        futbolargentino_played=[],
        espn_played=[],
    )

    assert len(prepared["played"]) == 90
    assert _lpf_results_fit_zones(zones, prepared["played"])
    assert prepared["inferred_played"] == []
    assert "La tabla implica 90 partidos" in prepared["coverage_note"]
    assert "LPF oficial aportó 45" in prepared["coverage_note"]


def test_prepare_automatic_update_milp_reconcilia_49_a_87_si_no_hay_feeds():
    """El respaldo grande puede resolver tres fechas, pero sólo si demuestra unicidad."""
    rng = random.Random(3867)
    by_pair = {
        (row["l"], row["v"]): (row["l"], row["v"], rng.randrange(4), rng.randrange(4))
        for row in LPF_FIXTURE if int(row["f"]) <= 6
    }
    round3 = [by_pair[(row["l"], row["v"])] for row in LPF_FIXTURE if int(row["f"]) <= 3]
    built_pairs = {
        ("Rosario Central", "Aldosivi"),
        ("Independiente Rivadavia", "Estudiantes de Río Cuarto"),
        ("Deportivo Riestra", "Estudiantes de La Plata"),
        ("Atlético Tucumán", "Sarmiento"),
    }
    baseline = round3 + [by_pair[pair] for pair in built_pairs]
    round4_5 = [by_pair[(row["l"], row["v"])] for row in LPF_FIXTURE if int(row["f"]) in {4, 5}]
    round6 = [by_pair[(row["l"], row["v"])] for row in LPF_FIXTURE if int(row["f"]) == 6]
    full = [*round3, *round4_5, *round6[:12]]
    zones = _zones_from_results(full)

    prepared = prepare_automatic_update(zones, builtin_played=baseline)

    assert len(prepared["played"]) == 87
    assert len(prepared["inferred_played"]) == 38
    assert _lpf_results_fit_zones(zones, prepared["played"])
    assert "solver demostró" in prepared["inferred_note"]


def test_prepare_automatic_update_tyc_completa_foto_de_nueve_fechas():
    """3.8.70: una fuente completa de TyC debe cerrar 135 sin ESPN ni FA."""
    full = _results_through_round(9, seed=3870)
    zones = _zones_from_results(full)
    baseline = full[:49]

    prepared = prepare_automatic_update(
        zones,
        builtin_played=baseline,
        tyc_played=full,
        official_played=[],
        futbolargentino_played=[],
        espn_played=[],
    )

    assert len(full) == 135
    assert len(prepared["played"]) == 135
    assert _lpf_results_fit_zones(zones, prepared["played"])
    assert "TyC Sports 135" in prepared["coverage_note"]
    assert prepared["inferred_played"] == []
