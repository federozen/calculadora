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
    """Reconstruye partidos faltantes sólo cuando la tabla fija una solución única.

    Es un respaldo determinístico para el caso en que el standings se actualiza antes
    que los feeds de marcadores. Compara la última foto validada contra la tabla nueva
    y busca, dentro del fixture oficial, una única combinación de partidos y marcadores
    que explique exactamente PJ, puntos, GF, GC y DG de *todos* los clubes.

    La búsqueda es deliberadamente conservadora, pero no usa un tope fijo de
    partidos faltantes: la complejidad real depende de cuántos cruces del fixture
    siguen siendo candidatos y de cuántas ramas sobreviven a los acumulados.

    - ningún club puede haber avanzado más de 2 PJ respecto de la base validada;
    - sólo considera la ventana de fechas consecutivas que empieza en la primera fecha
      todavía incompleta de la base;
    - la búsqueda tiene un presupuesto determinístico de estados para evitar bloquear
      una carga si la tabla deja demasiadas combinaciones abiertas;
    - si existen dos soluciones compatibles, no infiere nada.

    Esto permite conciliar, por ejemplo, el cierre de una fecha más un único partido de
    la siguiente sin convertir los PJ de la tabla en una fuente especulativa.
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
        if delta["dg"] != delta["gf"] - delta["ga"]:
            return [], ""
        if delta["pts"] > 3 * delta["pj"]:
            return [], ""
        # Si no sumó PJ, ningún otro acumulado puede haber cambiado.
        if delta["pj"] == 0 and any(
            delta[key] != 0 for key in ("pts", "gf", "ga", "dg")
        ):
            return [], ""
        deltas[team] = delta

    total_team_games = sum(delta["pj"] for delta in deltas.values())
    if total_team_games <= 0 or total_team_games % 2:
        return [], ""
    missing_matches = total_team_games // 2
    max_delta_pj = max((delta["pj"] for delta in deltas.values()), default=0)
    if max_delta_pj <= 0 or max_delta_pj > 2:
        return [], ""

    advanced = {team for team, delta in deltas.items() if delta["pj"] > 0}
    played_pairs = {(canon_club(l), canon_club(v)) for l, v, _gl, _gv in baseline}

    pending_edges = []
    for row in fixture or []:
        home = canon_club(row.get("l") or row.get("home") or "")
        away = canon_club(row.get("v") or row.get("away") or "")
        if not home or not away or (home, away) in played_pairs:
            continue
        if home not in advanced or away not in advanced:
            continue
        round_number = int(row.get("f") or row.get("round") or 0)
        if round_number > 0:
            pending_edges.append((round_number, home, away))

    if not pending_edges:
        return [], ""

    # No salta fechas enteras para fabricar una solución. Si un postergado rompe esta
    # continuidad y no hay un feed de resultados que lo identifique, se prefiere no inferir.
    first_pending_round = min(edge[0] for edge in pending_edges)
    last_candidate_round = first_pending_round + max_delta_pj - 1
    edges = [
        edge for edge in pending_edges
        if first_pending_round <= edge[0] <= last_candidate_round
    ]

    by_team = {team: [] for team in advanced}
    for idx, (_round, home, away) in enumerate(edges):
        by_team[home].append(idx)
        by_team[away].append(idx)
    if any(len(by_team.get(team, [])) < deltas[team]["pj"] for team in advanced):
        return [], ""
    if missing_matches > len(edges):
        return [], ""

    # La ventana ya está limitada a como máximo dos fechas por el guard de PJ.
    # En vez de cortar por una cantidad fija de partidos faltantes, el backtracking
    # usa un presupuesto de estados. Esto permite saltos reales como 49 -> 67
    # cuando los acumulados fijan rápidamente una solución, y abandona de forma
    # segura si la tabla deja un espacio combinatorio demasiado amplio.
    max_search_states = 250_000

    state = {
        team: {
            key: int(delta[key])
            for key in ("pj", "pts", "gf", "ga")
        }
        for team, delta in deltas.items()
    }
    used_edges = set()
    solutions = []
    search_states = 0
    search_aborted = False

    def team_state_is_possible(row):
        if any(int(row[key]) < 0 for key in ("pj", "pts", "gf", "ga")):
            return False
        if int(row["pts"]) > 3 * int(row["pj"]):
            return False
        if int(row["pj"]) == 0 and any(
            int(row[key]) != 0 for key in ("pts", "gf", "ga")
        ):
            return False
        return True

    def backtrack(current, chosen):
        nonlocal search_states, search_aborted
        if search_aborted or len(solutions) > 1:
            return
        search_states += 1
        if search_states > max_search_states:
            search_aborted = True
            return
        active = [team for team, row in current.items() if int(row["pj"]) > 0]
        if not active:
            if all(
                int(row["pts"]) == int(row["gf"]) == int(row["ga"]) == 0
                for row in current.values()
            ):
                solutions.append(list(chosen))
            return

        available_by_team = {}
        for team in active:
            available = [
                idx for idx in by_team.get(team, [])
                if idx not in used_edges
                and current[edges[idx][1]]["pj"] > 0
                and current[edges[idx][2]]["pj"] > 0
            ]
            if len(available) < int(current[team]["pj"]):
                return
            available_by_team[team] = available

        team = min(
            active,
            key=lambda value: (
                len(available_by_team[value]),
                int(current[value]["pj"]),
                value,
            ),
        )

        for edge_idx in available_by_team[team]:
            round_number, home, away = edges[edge_idx]
            if current[home]["pj"] <= 0 or current[away]["pj"] <= 0:
                continue

            max_home_goals = min(current[home]["gf"], current[away]["ga"])
            max_away_goals = min(current[home]["ga"], current[away]["gf"])
            for home_goals in range(int(max_home_goals) + 1):
                for away_goals in range(int(max_away_goals) + 1):
                    if home_goals > away_goals:
                        home_points, away_points = 3, 0
                    elif away_goals > home_goals:
                        home_points, away_points = 0, 3
                    else:
                        home_points = away_points = 1
                    if home_points > current[home]["pts"]:
                        continue
                    if away_points > current[away]["pts"]:
                        continue

                    nxt = {name: dict(row) for name, row in current.items()}
                    nxt[home]["pj"] -= 1
                    nxt[away]["pj"] -= 1
                    nxt[home]["pts"] -= home_points
                    nxt[away]["pts"] -= away_points
                    nxt[home]["gf"] -= home_goals
                    nxt[home]["ga"] -= away_goals
                    nxt[away]["gf"] -= away_goals
                    nxt[away]["ga"] -= home_goals
                    if not team_state_is_possible(nxt[home]) or not team_state_is_possible(nxt[away]):
                        continue
                    # Todos los goles de la tanda aparecen una vez como GF y una como GC.
                    if sum(row["gf"] for row in nxt.values()) != sum(
                        row["ga"] for row in nxt.values()
                    ):
                        continue

                    used_edges.add(edge_idx)
                    chosen.append(
                        (round_number, home, away, int(home_goals), int(away_goals))
                    )
                    backtrack(nxt, chosen)
                    chosen.pop()
                    used_edges.remove(edge_idx)
                    if len(solutions) > 1:
                        return

    backtrack(state, [])
    if search_aborted:
        return [], (
            "La conciliación determinística no se aplicó: la tabla deja demasiadas "
            "combinaciones de fixture/marcadores abiertas para resolverlas dentro del "
            "presupuesto seguro de búsqueda."
        )
    if len(solutions) != 1:
        if len(solutions) > 1:
            return [], (
                "La conciliación determinística no se aplicó: hay más de una "
                "combinación de resultados compatible con PJ, puntos, GF, GC y DG."
            )
        return [], ""

    solution_edges = solutions[0]
    inferred = sorted(
        [(home, away, gh, ga) for _rnd, home, away, gh, ga in solution_edges],
        key=lambda row: (row[0], row[1]),
    )
    candidate = _merge_lpf_results(baseline, inferred)
    if not _lpf_results_fit_zones(zones, candidate):
        return [], ""

    rounds = sorted({int(row[0]) for row in solution_edges})
    if len(rounds) == 1:
        round_label = f"Fecha {rounds[0]}"
    else:
        round_label = "Fechas " + "-".join(str(value) for value in (rounds[0], rounds[-1]))
    details = "; ".join(f"{h} {gh}-{ga} {a}" for h, a, gh, ga in inferred)
    note = (
        f"Conciliación por tabla ({round_label}): {details}. "
        f"Los {len(inferred)} marcador(es) surgen de una única combinación del fixture "
        "y reproducen exactamente PJ, puntos, GF, GC y DG."
    )
    return inferred, note

