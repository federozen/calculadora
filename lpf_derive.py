"""Derivación e inferencia de datos.

Reconstruye la foto del Apertura desde la tabla anual y las zonas actuales, e infiere
resultados de partidos faltantes a partir de las diferencias entre tablas y el fixture
conocido. Lógica pura (datos -> datos), parte de la garantía de que la calculadora
"toma bien los datos" antes de contar.
"""
from __future__ import annotations

from lpf_text import _zlow
from lpf_clubs import canon_club
from lpf_data_2026 import LPF_FIXTURE
from lpf_reconcile import _lpf_result_stats, _lpf_results_fit_zones, _merge_lpf_results


def _asignar_nombres(claves, equipos):
    """Empareja nombres externos con los equipos cargados sin confundir casos como
    «Estudiantes» vs «Estudiantes RC» o «Gimnasia» vs «Gimnasia (M)».
    1) primero los exactos, 2) después los parciales solo si son únicos y el equipo sigue libre."""
    libres = list(equipos); out = {}
    for k in list(claves):
        for e in list(libres):
            if _zlow(k) == _zlow(e):
                out[k] = e; libres.remove(e); break
    for k in [x for x in claves if x not in out]:
        kn = _zlow(k)
        cands = [e for e in libres if kn in _zlow(e) or _zlow(e) in kn]
        if len(cands) == 1:
            out[k] = cands[0]; libres.remove(cands[0])
    return out


def derivar_apertura(anual, Z):
    """Apertura = Anual − lo que ya se jugó del Clausura, para que la anual siga viva
    a medida que avanzan las fechas (y no quede congelada en la foto pegada)."""
    clausura = {}
    for lab, b in (Z or {}).items():
        clausura.update(b)
    asign = _asignar_nombres(list(anual.keys()), list(clausura.keys()))
    out, avisos = {}, []
    for nombre, d in anual.items():
        e = asign.get(nombre)
        c = clausura.get(e, {}) if e else {}
        ap = {k: d.get(k, 0) - c.get(k, 0) for k in ("pts", "pj", "dg", "gf", "ga")}
        if ap["pts"] < 0 or ap["pj"] < 0:
            avisos.append(f"{nombre}: la anual pegada tiene menos que el Clausura cargado; revisá que sean de la misma fecha.")
            ap = {k: max(0, v) for k, v in ap.items()}
        out[e or nombre] = ap
    pjs = sorted({d["pj"] for d in out.values()})
    if len(pjs) > 1:
        avisos.append(f"⚠️ El Apertura derivado da distinta cantidad de partidos según el equipo ({pjs}). "
                      "Casi seguro pegaste la **anual y el Clausura de fechas distintas**: tienen que ser del mismo momento.")
    elif pjs and pjs[0] != 16:
        avisos.append(f"⚠️ El Apertura derivado da {pjs[0]} partidos y la fase de zonas del Apertura fueron 16 fechas. "
                      "Revisá que la anual y las tablas del Clausura sean de la misma fecha.")
    return out, avisos

def _lpf_infer_missing_results(zones, baseline, fixture=None):
    """Reconstruye uno o varios partidos faltantes sólo si la tabla los fija de forma única.

    Se usa cuando el standings avanzó antes que las fuentes de marcadores. Respecto de una
    foto histórica ya validada, cada club que avanzó debe haber sumado exactamente un PJ.
    Sus deltas de puntos, GF, GC y DG fijan el marcador. Después se busca en el fixture una
    única combinación de cruces pendientes que empareje a todos esos clubes una sola vez.
    Si hay dos soluciones posibles, un delta incoherente o algún club avanzó más de un PJ,
    no se infiere nada.
    """
    fixture = fixture or LPF_FIXTURE
    baseline = _merge_lpf_results(baseline)
    if not zones or not baseline or _lpf_results_fit_zones(zones, baseline):
        return [], ""

    expected = {}
    for base in (zones or {}).values():
        for team, row in (base or {}).items():
            expected[canon_club(team)] = {
                key: int((row or {}).get(key, 0))
                for key in ("pj", "pts", "gf", "ga", "dg")
            }
    actual = _lpf_result_stats(baseline)
    deltas = {}
    for team, wanted in expected.items():
        got = actual.get(team, {"pj": 0, "pts": 0, "gf": 0, "ga": 0, "dg": 0})
        delta = {key: int(wanted[key]) - int(got.get(key, 0)) for key in wanted}
        if any(delta[key] < 0 for key in ("pj", "pts", "gf", "ga")):
            return [], ""
        # Si no sumó PJ, ningún otro acumulado puede haber cambiado.
        if delta["pj"] == 0 and any(delta[key] != 0 for key in ("pts", "gf", "ga", "dg")):
            return [], ""
        deltas[team] = delta

    advanced = sorted(team for team, delta in deltas.items() if delta["pj"] != 0)
    if not advanced or len(advanced) % 2:
        return [], ""
    # Respaldo deliberadamente conservador: una sola tanda de partidos nuevos.
    if any(deltas[team]["pj"] != 1 for team in advanced):
        return [], ""

    played_pairs = {(canon_club(l), canon_club(v)) for l, v, _gl, _gv in baseline}
    advanced_set = set(advanced)
    edges = []
    for row in fixture or []:
        home = canon_club(row.get("l") or row.get("home") or "")
        away = canon_club(row.get("v") or row.get("away") or "")
        if not home or not away or (home, away) in played_pairs:
            continue
        if home not in advanced_set or away not in advanced_set:
            continue

        gh = deltas[home]["gf"]
        ga = deltas[home]["ga"]
        if gh < 0 or ga < 0:
            continue
        if deltas[away]["gf"] != ga or deltas[away]["ga"] != gh:
            continue
        if deltas[home]["dg"] != gh - ga or deltas[away]["dg"] != ga - gh:
            continue
        if gh > ga:
            pts_home, pts_away = 3, 0
        elif ga > gh:
            pts_home, pts_away = 0, 3
        else:
            pts_home = pts_away = 1
        if deltas[home]["pts"] != pts_home or deltas[away]["pts"] != pts_away:
            continue
        round_number = int(row.get("f") or row.get("round") or 0)
        edges.append((round_number, home, away, int(gh), int(ga)))

    # La tanda nueva debe pertenecer a una misma fecha oficial. Esto evita que
    # deltas iguales armen combinaciones ficticias con cruces de fechas futuras.
    # Si el feed quedó atrasado más de una fecha, este respaldo no intenta adivinar.
    solutions = []
    for candidate_round in sorted({edge[0] for edge in edges if edge[0] > 0}):
        round_edges = [edge for edge in edges if edge[0] == candidate_round]
        by_team = {team: [] for team in advanced}
        for edge in round_edges:
            _rnd, home, away, _gh, _ga = edge
            by_team[home].append(edge)
            by_team[away].append(edge)
        if any(not by_team[team] for team in advanced):
            continue

        round_solutions = []
        def backtrack(remaining, chosen):
            if len(round_solutions) > 1:
                return
            if not remaining:
                round_solutions.append(list(chosen))
                return
            team = min(remaining, key=lambda t: len([
                e for e in by_team[t]
                if e[1] in remaining and e[2] in remaining
            ]))
            candidates = [
                e for e in by_team[team]
                if e[1] in remaining and e[2] in remaining
            ]
            for edge in candidates:
                _rnd, home, away, _gh, _ga = edge
                backtrack(remaining - {home, away}, chosen + [edge])
                if len(round_solutions) > 1:
                    return

        backtrack(set(advanced), [])
        for solution in round_solutions[:2]:
            solutions.append((candidate_round, solution))
            if len(solutions) > 1:
                break
        if len(solutions) > 1:
            break

    if len(solutions) != 1:
        return [], ""

    inferred_round, solution_edges = solutions[0]
    inferred = sorted(
        [(home, away, gh, ga) for _rnd, home, away, gh, ga in solution_edges],
        key=lambda row: (row[0], row[1]),
    )
    candidate = _merge_lpf_results(baseline, inferred)
    if not _lpf_results_fit_zones(zones, candidate):
        return [], ""

    details = "; ".join(f"{h} {gh}-{ga} {a}" for h, a, gh, ga in inferred)
    note = (
        f"Conciliación por tabla (Fecha {inferred_round}): {details}. "
        f"Los {len(inferred)} marcador(es) surgen de una única combinación de esa fecha "
        "y reproducen exactamente PJ, puntos, GF, GC y DG."
    )
    return inferred, note
