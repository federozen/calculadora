"""Foto canónica de competencia reutilizable por Streamlit y futuras APIs.

La foto reúne datos ya normalizados/reconciliados en una estructura simple y
serializable. No hace red, no conoce Streamlit y no calcula fórmulas nuevas: usa
``lpf_state`` como única construcción autoritativa del estado.
"""
from __future__ import annotations

LPF_RUNTIME_API = 6
SNAPSHOT_SCHEMA_VERSION = "1"


from collections.abc import Mapping, Sequence
from typing import Any

from lpf_pisos import promedio_totales
from lpf_state import build_lpf_state


def _average_rows(previous: Mapping[str, object] | None) -> dict[str, dict[str, int]]:
    """Normaliza antecedentes de promedios al esquema JSON ``points/played``."""
    out: dict[str, dict[str, int]] = {}
    for team, raw in (previous or {}).items():
        if isinstance(raw, Mapping):
            pts = int(raw.get("pts", raw.get("points", 0)))
            pj = int(raw.get("pj", raw.get("played", 0)))
        elif isinstance(raw, (tuple, list)) and len(raw) >= 2:
            pts, pj = int(raw[0]), int(raw[1])
        else:
            continue
        out[str(team)] = {"points": pts, "played": pj}
    return out


def build_competition_snapshot(
    zones: Mapping[str, Mapping[str, Mapping[str, object]]],
    *,
    played: Sequence[tuple[str, str, int, int]] | None = None,
    annual: Mapping[str, Mapping[str, object]] | None = None,
    opening: Mapping[str, Mapping[str, object]] | None = None,
    previous_averages: Mapping[str, object] | None = None,
    fixture: Sequence[Mapping[str, object]] = (),
    annual_relegations: int = 1,
    average_relegations: int = 1,
) -> tuple[dict[str, Any], object]:
    """Construye una foto estable a partir del mismo estado que usa la app."""
    state, report = build_lpf_state(
        zones,
        played=played,
        annual_direct=annual,
        opening=opening,
        promedios=previous_averages,
        fixture=fixture,
        n_anual=annual_relegations,
        n_prom=average_relegations,
    )
    snapshot = {
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "competition": "LPF 2026",
        "teams": list(state["equipos"]),
        "zones": state["zonas_lpf"],
        "annual": state["anual_directo"],
        "opening": state["apertura"],
        "played": [
            {"home": h, "away": a, "home_goals": int(gh), "away_goals": int(ga)}
            for h, a, gh, ga in state["jugados"]
        ],
        "pending": [
            {"home": h, "away": a}
            for h, a in state["pendientes"]
        ],
        "remaining": {team: int(value) for team, value in state["rest"].items()},
        "previous_averages": _average_rows(state.get("promedios") or previous_averages),
        "fixture": [dict(game) for game in fixture],
        "rules": {
            "annual_relegations": int(state["n_anual"]),
            "average_relegations": int(state["n_prom"]),
        },
    }
    return snapshot, report


def snapshot_scope(
    snapshot: Mapping[str, object],
    scope: str,
    *,
    zone: str | None = None,
) -> tuple[Mapping[str, object], Mapping[str, int], list[tuple[str, str]]]:
    """Devuelve base, partidos restantes y conteos para una consulta del snapshot."""
    remaining = snapshot.get("remaining")
    pending_raw = snapshot.get("pending")
    if not isinstance(remaining, Mapping) or not isinstance(pending_raw, Sequence):
        raise ValueError("snapshot incompleto")

    pending: list[tuple[str, str]] = []
    for row in pending_raw:
        if not isinstance(row, Mapping):
            continue
        home, away = str(row.get("home", "")), str(row.get("away", ""))
        if home and away:
            pending.append((home, away))

    if scope == "annual":
        base = snapshot.get("annual")
        if not isinstance(base, Mapping):
            raise ValueError("snapshot sin Tabla Anual")
        return base, remaining, pending

    if scope == "zone":
        zones = snapshot.get("zones")
        if not isinstance(zones, Mapping) or zone not in zones:
            raise ValueError("zona inexistente")
        base = zones[zone]
        if not isinstance(base, Mapping):
            raise ValueError("zona inválida")
        pool = set(base)
        matches = [(h, a) for h, a in pending if h in pool or a in pool]
        return base, remaining, matches

    raise ValueError("scope inválido")


def snapshot_average_totals(snapshot: Mapping[str, object]) -> dict[str, tuple[int, int]] | None:
    """Totales de promedios listos para ``piso_no_descenso``."""
    annual = snapshot.get("annual")
    zones = snapshot.get("zones")
    previous = snapshot.get("previous_averages")
    if not isinstance(annual, Mapping) or not isinstance(zones, Mapping) or not isinstance(previous, Mapping):
        return None
    return promedio_totales(annual, zones, previous)
