"""Regresiones de las primitivas Monte Carlo extraídas del archivo Streamlit."""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

from lpf_simulation import objective_mask, simulate_point_additions, simulate_zone_rank_points

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "lpf_simulation.py"
MAIN = ROOT / "calculadora_futbol_argentino.py"


def test_modulo_no_depende_de_streamlit_ni_red():
    text = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "streamlit" not in imported
    assert "requests" not in imported
    assert "session_state" not in text


def test_simulacion_de_zona_es_reproducible_y_devuelve_puntos_enteros():
    base = {
        "A": {"pts": 10, "dg": 2},
        "B": {"pts": 9, "dg": 0},
        "C": {"pts": 7, "dg": -1},
        "D": {"pts": 6, "dg": 1},
    }
    remaining = {team: 2 for team in base}
    pending = [("A", "B"), ("C", "D")]
    strength = {"A": 1.2, "B": 1.05, "C": 0.95, "D": 0.85}
    first = simulate_zone_rank_points(base, remaining, pending, "A", 500, 41, strength)
    second = simulate_zone_rank_points(base, remaining, pending, "A", 500, 41, strength)
    np.testing.assert_array_equal(first[0], second[0])
    np.testing.assert_array_equal(first[1], second[1])
    assert first[0].shape == first[1].shape == (500,)
    assert np.issubdtype(first[1].dtype, np.integer)


def test_resultados_forzados_en_suma_de_puntos_son_deterministas():
    teams = ["A", "B", "C"]
    pending = [("A", "B"), ("B", "C")]
    strength = {team: 1.0 for team in teams}
    additions, idx = simulate_point_additions(
        teams,
        pending,
        strength,
        40,
        7,
        forced={("A", "B"): "L", ("B", "C"): "E"},
    )
    assert np.all(additions[:, idx["A"]] == 3)
    assert np.all(additions[:, idx["B"]] == 1)
    assert np.all(additions[:, idx["C"]] == 1)


def test_mascara_de_playoffs_respeta_top_ocho():
    teams = [f"T{i}" for i in range(10)]
    context = {
        "zona_de": {team: "A" for team in teams},
        "Z": {"A": {team: {} for team in teams}},
        "zpts": {team: 20 - i for i, team in enumerate(teams)},
        "zdg": {team: 0 for team in teams},
    }
    additions = np.zeros((3, len(teams)))
    idx = {team: i for i, team in enumerate(teams)}
    assert objective_mask("playoffs", "T0", additions, idx, context).tolist() == [True, True, True]
    assert objective_mask("playoffs", "T9", additions, idx, context).tolist() == [False, False, False]


def test_main_delega_primitivas_generales_al_modulo_puro():
    text = MAIN.read_text(encoding="utf-8")
    assert "simulate_point_additions as _sim_lpf_add" in text
    assert "objective_mask as _obj_bool" in text
    assert "simulate_zone_rank_points as _simulate_zone_rank_points_core" in text
    assert "def _sim_lpf_add(" not in text
    assert "def _obj_bool(" not in text
