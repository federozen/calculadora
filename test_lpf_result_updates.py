"""Regresiones para la aplicación pura de marcadores cargados desde la UI."""
from __future__ import annotations

import copy
import random

from lpf_result_updates import apply_completed_results, table_position_changes
from lpf_standings import liga_tabla_df


def _row(pts=0, pj=0, gf=0, ga=0):
    return {"pts": pts, "pj": pj, "gf": gf, "ga": ga, "dg": gf - ga}


def _reference_apply(zones, played, pending, results):
    zones = copy.deepcopy(zones or {})
    played = list(played or [])
    pending = set(pending or [])
    applied = []
    known = {(l, v) for l, v, _gl, _gv in played}
    for local, visitor, gl, gv in results:
        if (local, visitor) not in pending or (local, visitor) in known:
            continue
        for team, gf, ga in ((local, gl, gv), (visitor, gv, gl)):
            for base in zones.values():
                if team in base:
                    stats = base[team]
                    stats["pj"] = int(stats.get("pj", 0)) + 1
                    stats["gf"] = int(stats.get("gf", 0)) + int(gf)
                    stats["ga"] = int(stats.get("ga", 0)) + int(ga)
                    stats["dg"] = stats["gf"] - stats["ga"]
                    stats["pts"] = int(stats.get("pts", 0)) + (3 if gf > ga else 1 if gf == ga else 0)
                    break
        played.append((local, visitor, int(gl), int(gv)))
        known.add((local, visitor))
        applied.append((local, visitor, int(gl), int(gv)))
    return zones, played, applied


def _reference_changes(before_zones, before_annual, after_zones, after_annual):
    changes = []
    before_zone = {lab: liga_tabla_df(base) for lab, base in before_zones.items()}
    for lab, base in after_zones.items():
        old = {r["Equipo"]: int(r["Pos"]) for _, r in before_zone[lab].iterrows()}
        new_df = liga_tabla_df(base)
        for _, row in new_df.iterrows():
            team = row["Equipo"]
            if old.get(team) != int(row["Pos"]):
                changes.append({"Tabla": f"Zona {lab}", "Equipo": team,
                                "Antes": old.get(team), "Ahora": int(row["Pos"]),
                                "Cambio": int(old.get(team, row["Pos"])) - int(row["Pos"])})
    before_annual_df = liga_tabla_df(before_annual)
    if not before_annual_df.empty and after_annual:
        old = {r["Equipo"]: int(r["Pos"]) for _, r in before_annual_df.iterrows()}
        for _, row in liga_tabla_df(after_annual).iterrows():
            team = row["Equipo"]
            if old.get(team) != int(row["Pos"]):
                changes.append({"Tabla": "Anual", "Equipo": team,
                                "Antes": old.get(team), "Ahora": int(row["Pos"]),
                                "Cambio": int(old.get(team, row["Pos"])) - int(row["Pos"])})
    return changes


def test_apply_completed_results_ignora_no_pendientes_y_duplicados():
    zones = {"A": {"A": _row(), "B": _row()}, "B": {"C": _row(), "D": _row()}}
    played = [("A", "B", 1, 0)]
    pending = [("C", "D")]
    results = [("A", "B", 9, 9), ("C", "D", 2, 2), ("C", "D", 4, 0)]
    updated, played_out, applied = apply_completed_results(zones, played, pending, results)
    assert applied == [("C", "D", 2, 2)]
    assert played_out == played + applied
    assert updated["B"]["C"]["pts"] == 1
    assert updated["B"]["D"]["pts"] == 1
    assert zones["B"]["C"]["pj"] == 0  # no muta la entrada


def test_table_position_changes_informa_zona_y_anual():
    before_zones = {"A": {"A": _row(3, 1, 1, 0), "B": _row(0, 1, 0, 1)}}
    after_zones = {"A": {"A": _row(3, 2, 1, 2), "B": _row(3, 2, 2, 1)}}
    before_annual = copy.deepcopy(before_zones["A"])
    after_annual = copy.deepcopy(after_zones["A"])
    changes = table_position_changes(before_zones, before_annual, after_zones, after_annual)
    assert {row["Tabla"] for row in changes} == {"Zona A", "Anual"}
    assert {row["Equipo"] for row in changes} == {"A", "B"}


def test_apply_completed_results_equivale_al_codigo_3821_en_500_casos():
    rng = random.Random(3821)
    teams = [f"T{i}" for i in range(8)]
    all_pairs = [(teams[i], teams[j]) for i in range(0, 8, 2) for j in [i + 1]]
    for _ in range(500):
        zones = {
            "A": {t: _row(rng.randint(0, 20), rng.randint(0, 8), rng.randint(0, 15), rng.randint(0, 15)) for t in teams[:4]},
            "B": {t: _row(rng.randint(0, 20), rng.randint(0, 8), rng.randint(0, 15), rng.randint(0, 15)) for t in teams[4:]},
        }
        for base in zones.values():
            for row in base.values():
                row["dg"] = row["gf"] - row["ga"]
        shuffled = all_pairs[:]
        rng.shuffle(shuffled)
        played_pairs = shuffled[:rng.randint(0, 2)]
        pending = [pair for pair in all_pairs if pair not in played_pairs]
        played = [(l, v, rng.randint(0, 4), rng.randint(0, 4)) for l, v in played_pairs]
        candidates = all_pairs + all_pairs[:2]
        rng.shuffle(candidates)
        results = [(l, v, rng.randint(0, 5), rng.randint(0, 5)) for l, v in candidates]
        assert apply_completed_results(zones, played, pending, results) == _reference_apply(zones, played, pending, results)


def test_table_position_changes_equivale_al_codigo_3821_en_300_casos():
    rng = random.Random(1738)
    for _ in range(300):
        before_zones = {"A": {}, "B": {}}
        after_zones = {"A": {}, "B": {}}
        for i in range(10):
            label = "A" if i < 5 else "B"
            team = f"T{i}"
            pts = rng.randint(0, 20)
            gf = rng.randint(0, 15)
            ga = rng.randint(0, 15)
            before_zones[label][team] = _row(pts, rng.randint(0, 8), gf, ga)
            add = rng.choice([0, 1, 3])
            after = copy.deepcopy(before_zones[label][team])
            after["pts"] += add
            after["pj"] += int(add != 0)
            after["gf"] += rng.randint(0, 2)
            after["ga"] += rng.randint(0, 2)
            after["dg"] = after["gf"] - after["ga"]
            after_zones[label][team] = after
        before_annual = {team: copy.deepcopy(row) for base in before_zones.values() for team, row in base.items()}
        after_annual = {team: copy.deepcopy(row) for base in after_zones.values() for team, row in base.items()}
        assert table_position_changes(before_zones, before_annual, after_zones, after_annual) == _reference_changes(
            before_zones, before_annual, after_zones, after_annual
        )


def test_modulo_no_depende_de_streamlit_ni_red():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "lpf_result_updates.py").read_text(encoding="utf-8")
    assert "import streamlit" not in source
    assert "import requests" not in source
