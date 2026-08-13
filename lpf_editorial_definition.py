"""Salidas editoriales exactas para la definición de objetivos LPF.

Este módulo no conoce Streamlit ni proveedores. Convierte los condicionales exactos
por fecha en estructuras cortas para matrices, semáforos, zona de pelea y reloj de
definición. No calcula probabilidades.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from lpf_conditionals import next_round_conditionals
from lpf_standings import liga_tabla_df

LPF_RUNTIME_API = 16


def branch_state(branch: Mapping[str, object]) -> dict[str, str]:
    """Resume una rama G/E/P sin convertir frecuencias en probabilidades."""
    total = max(1, int(branch.get("total_combinations", 0) or 0))
    inside = int(branch.get("season_in", 0) or 0)
    open_ = int(branch.get("season_pelea", 0) or 0)
    outside = int(branch.get("season_out", 0) or 0)
    condition = str(branch.get("sufficient_condition") or "").strip()

    if inside == total:
        return {"signal": "green", "label": "Asegura", "detail": "No depende de otros resultados"}
    if outside == total:
        return {"signal": "red", "label": "Queda eliminado", "detail": "No hay otra cancha que lo salve"}
    if inside:
        detail = condition if condition and condition != "No depende de otros resultados" else "Existe una combinación exacta favorable"
        return {"signal": "yellow", "label": "Puede asegurar", "detail": detail}
    if outside and open_:
        return {"signal": "yellow", "label": "Puede quedar eliminado", "detail": "Depende de otros resultados"}
    if int(branch.get("round_safe", 0) or 0):
        detail = condition if condition and condition != "No depende de otros resultados" else "Puede terminar la fecha dentro"
        return {"signal": "yellow", "label": "Sigue abierto", "detail": detail}
    return {"signal": "yellow", "label": "Sigue dependiendo", "detail": "La fecha no resuelve el objetivo"}


def branch_cell(branch: Mapping[str, object], *, with_detail: bool = True) -> str:
    state = branch_state(branch)
    icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[state["signal"]]
    if with_detail and state["detail"]:
        return f"{icon} {state['label']} · {state['detail']}"
    return f"{icon} {state['label']}"


def all_teams_matrix(
    base: Mapping[str, Mapping[str, object]],
    rest: Mapping[str, int],
    games: Iterable[tuple[str, str]],
    teams: Sequence[str],
    cutoff: int,
    *,
    max_other_matches: int = 8,
) -> list[dict[str, object]]:
    """Una fila por equipo y tres columnas G/E/P con estado matemático exacto."""
    rows: list[dict[str, object]] = []
    for team in teams:
        if team not in base:
            continue
        report = next_round_conditionals(
            base, rest, games, team, cutoff, max_other_matches=max_other_matches
        )
        row: dict[str, object] = {
            "Equipo": team,
            "PTS": int((base[team] or {}).get("pts", 0)),
            "PJ por jugar": int(rest.get(team, 0)),
        }
        if not report.get("available"):
            row.update({"Si gana": "—", "Si empata": "—", "Si pierde": "—", "_report": report})
        else:
            by_result = {str(branch["result"]): branch for branch in report.get("branches", [])}
            row.update({
                "Si gana": branch_cell(by_result["G"]),
                "Si empata": branch_cell(by_result["E"]),
                "Si pierde": branch_cell(by_result["P"]),
                "_report": report,
            })
        rows.append(row)
    return rows


def fight_zone(
    base: Mapping[str, Mapping[str, object]],
    rest: Mapping[str, int],
    team: str,
    cutoff: int,
    *,
    radius: int = 2,
) -> list[dict[str, object]]:
    """Recorta la tabla alrededor del equipo y del corte del objetivo."""
    if team not in base or cutoff <= 0:
        return []
    frame = liga_tabla_df(base)
    order = list(frame["Equipo"])
    if team not in order:
        return []
    team_pos = order.index(team) + 1
    cutoff = min(int(cutoff), len(order))
    keep: set[int] = set()
    for center in (team_pos, cutoff):
        keep.update(range(max(1, center - radius), min(len(order), center + radius) + 1))
    rows: list[dict[str, object]] = []
    previous = None
    for pos in sorted(keep):
        if previous is not None and pos > previous + 1:
            rows.append({"Pos": "…", "Equipo": "…", "PTS": "…", "PJ por jugar": "…", "Techo": "…", "Referencia": ""})
        record = frame.iloc[pos - 1]
        name = str(record["Equipo"])
        refs = []
        if pos == cutoff:
            refs.append("corte")
        if name == team:
            refs.append("seleccionado")
        pts = int(record["PTS"])
        left = int(rest.get(name, 0))
        rows.append({
            "Pos": f"{pos}º",
            "Equipo": name,
            "PTS": pts,
            "PJ por jugar": left,
            "Techo": pts + 3 * left,
            "Referencia": " · ".join(refs),
        })
        previous = pos
    return rows


def definition_clock(
    report: Mapping[str, object] | None,
    *,
    current_points: int,
    guarantee: int | None = None,
    guarantee_round_label: str | None = None,
) -> list[dict[str, str]]:
    """Hitos exactos y breves para una línea temporal editorial.

    El primer hito sale de la próxima fecha enumerada. El segundo, si existe, sólo
    dice cuándo el equipo puede alcanzar por sus propios puntos un total que ya fue
    demostrado como garantía exacta.
    """
    milestones: list[dict[str, str]] = []
    if report and report.get("available"):
        branches = list(report.get("branches", []))
        can_in = [b for b in branches if int(b.get("season_in", 0) or 0) > 0]
        sure_in = [b for b in branches if int(b.get("season_in", 0) or 0) == max(1, int(b.get("total_combinations", 0) or 0))]
        can_out = [b for b in branches if int(b.get("season_out", 0) or 0) > 0]
        if sure_in:
            labels = ", ".join(str(b.get("result_label", "")) for b in sure_in)
            milestones.append({"when": "Próxima fecha", "status": "Puede asegurar", "detail": f"{labels}: no depende de nadie."})
        elif can_in:
            best = can_in[0]
            condition = str(best.get("sufficient_condition") or "hay una combinación favorable")
            milestones.append({"when": "Próxima fecha", "status": "Puede asegurar", "detail": f"{best.get('result_label')}: {condition}."})
        if can_out:
            labels = ", ".join(str(b.get("result_label", "")) for b in can_out)
            milestones.append({"when": "Próxima fecha", "status": "Puede quedar eliminado", "detail": labels})
        if not can_in and not can_out:
            milestones.append({"when": "Próxima fecha", "status": "No puede definirse", "detail": "El objetivo seguirá abierto pase lo que pase en esta fecha."})

    if guarantee is not None and int(guarantee) > int(current_points):
        needed = int(guarantee) - int(current_points)
        wins = (needed + 2) // 3
        label = guarantee_round_label or f"Tras {wins} partido(s) propios"
        milestones.append({
            "when": label,
            "status": "Puede llegar al total que asegura",
            "detail": f"Necesita sumar al menos {needed} puntos para alcanzar {int(guarantee)}.",
        })
    elif guarantee is not None and int(guarantee) <= int(current_points):
        milestones.append({"when": "Hoy", "status": "Ya alcanzó el total que asegura", "detail": f"Tiene {int(current_points)} puntos; la garantía exacta es {int(guarantee)}."})
    return milestones
