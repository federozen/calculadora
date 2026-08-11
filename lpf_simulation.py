"""Primitivas Monte Carlo puras para la LPF.

No conoce Streamlit, red ni estado global de la aplicación. Recibe fuerzas,
fixture pendiente y contexto de competencia por parámetro y devuelve arrays NumPy
que las capas superiores convierten en probabilidades o narrativas.
"""
from __future__ import annotations

import numpy as np

LPF_RUNTIME_API = 10

DEFAULT_DRAW_PROBABILITY = 0.26
DEFAULT_HOME_ADVANTAGE = 1.22


def simulate_zone_rank_points(
    base,
    remaining,
    pending,
    target,
    n,
    seed,
    strength,
    forced=None,
    pdraw=DEFAULT_DRAW_PROBABILITY,
    loc=DEFAULT_HOME_ADVANTAGE,
):
    """Simula posición y puntos finales de ``target`` dentro de su zona."""
    rng = np.random.default_rng(seed)
    teams = list(base.keys())
    idx = {team: i for i, team in enumerate(teams)}
    points = np.tile(np.array([base[team]["pts"] for team in teams], float), (n, 1))
    dg0 = np.array([float(base[team].get("dg", 0)) for team in teams])
    forced = dict(forced or {})
    consumed = {team: 0 for team in teams}

    for (local, visitor), outcome in forced.items():
        for team in (local, visitor):
            if team in idx:
                consumed[team] += 1
        if outcome == "L" and local in idx:
            points[:, idx[local]] += 3
        elif outcome == "V" and visitor in idx:
            points[:, idx[visitor]] += 3
        elif outcome == "E":
            if local in idx:
                points[:, idx[local]] += 1
            if visitor in idx:
                points[:, idx[visitor]] += 1

    in_fixture = {team: 0 for team in teams}
    for local, visitor in pending:
        if local in idx and visitor in idx and (local, visitor) not in forced:
            in_fixture[local] += 1
            in_fixture[visitor] += 1
            p_local = (1 - pdraw) * (strength[local] * loc) / (strength[local] * loc + strength[visitor])
            sample = rng.random(n)
            local_win = sample < p_local
            visitor_win = sample >= p_local + pdraw
            points[:, idx[local]] += np.where(local_win, 3, np.where(visitor_win, 0, 1))
            points[:, idx[visitor]] += np.where(visitor_win, 3, np.where(local_win, 0, 1))

    for team in teams:
        extra = max(0, remaining.get(team, 0) - in_fixture[team] - consumed[team])
        if extra:
            p_team = (1 - pdraw) * strength[team] / (strength[team] + 1.0)
            sample = rng.random((n, extra))
            points[:, idx[team]] += np.where(
                sample < p_team,
                3,
                np.where(sample < p_team + pdraw, 1, 0),
            ).sum(axis=1)

    key = points + dg0[None, :] * 1e-4 + rng.random((n, len(teams))) * 1e-7
    positions = np.argsort(np.argsort(-key, axis=1), axis=1) + 1
    return positions[:, idx[target]], points[:, idx[target]].astype(int)


def simulate_point_additions(
    teams,
    pending,
    strength,
    n,
    seed,
    forced=None,
    pdraw=DEFAULT_DRAW_PROBABILITY,
    loc=DEFAULT_HOME_ADVANTAGE,
):
    """Simula los puntos que suma cada equipo en todos los partidos pendientes."""
    rng = np.random.default_rng(seed)
    idx = {team: i for i, team in enumerate(teams)}
    add = np.zeros((n, len(teams)))
    forced = forced or {}
    for local, visitor in pending:
        if local not in idx or visitor not in idx:
            continue
        ilocal, ivisitor = idx[local], idx[visitor]
        outcome = forced.get((local, visitor))
        if outcome == "L":
            add[:, ilocal] += 3
        elif outcome == "V":
            add[:, ivisitor] += 3
        elif outcome == "E":
            add[:, ilocal] += 1
            add[:, ivisitor] += 1
        else:
            p_local = (1 - pdraw) * (strength[local] * loc) / (strength[local] * loc + strength[visitor])
            sample = rng.random(n)
            local_win = sample < p_local
            visitor_win = sample >= p_local + pdraw
            add[:, ilocal] += np.where(local_win, 3, np.where(visitor_win, 0, 1))
            add[:, ivisitor] += np.where(visitor_win, 3, np.where(local_win, 0, 1))
    return add, idx


def objective_mask(objective, team, additions, idx, context):
    """Indica en cada corrida si ``team`` cumple el objetivo pedido."""
    n = additions.shape[0]
    if objective == "playoffs":
        zone = context["zona_de"].get(team)
        if not zone:
            return np.zeros(n, bool)
        zone_teams = list(context["Z"][zone])
        eps = np.arange(len(zone_teams), dtype=float) * 1e-8
        key = (
            np.array([context["zpts"][other] + context["zdg"][other] * 1e-4 for other in zone_teams])[None, :]
            + eps
            + additions[:, [idx[other] for other in zone_teams]]
        )
        target_index = zone_teams.index(team)
        return ((key > key[:, target_index:target_index + 1]).sum(1) + 1) <= 8

    if objective in ("libertadores", "sudamericana", "al_menos_sudamericana"):
        reduced = context["reducida"]
        if team not in reduced:
            return np.zeros(n, bool)
        eps = np.arange(len(reduced), dtype=float) * 1e-8
        key = (
            np.array([context["apts"][other] + context["adg"][other] * 1e-4 for other in reduced])[None, :]
            + eps
            + additions[:, [idx[other] for other in reduced]]
        )
        target_index = reduced.index(team)
        rank = (key > key[:, target_index:target_index + 1]).sum(1) + 1
        if objective == "libertadores":
            return rank <= context["n_lib"]
        if objective == "al_menos_sudamericana":
            return rank <= context["n_lib"] + 6
        return (rank > context["n_lib"]) & (rank <= context["n_lib"] + 6)

    if objective == "descenso":
        averages = context["prom"]
        remaining = context["rest"]
        average_teams = [other for other in context["equipos"] if other in averages]
        if average_teams:
            numerator = (
                np.array([averages[other][0] for other in average_teams], float)[None, :]
                + additions[:, [idx[other] for other in average_teams]]
            )
            denominator = np.array(
                [averages[other][1] + remaining.get(other, 0) for other in average_teams],
                float,
            )[None, :]
            average_value = numerator / denominator
            average_last = np.array(average_teams)[average_value.argmin(1)]
        else:
            average_last = np.array([""] * n)

        annual_teams = [other for other in context["equipos"] if other in context["apts"]]
        eps = np.arange(len(annual_teams), dtype=float) * 1e-8
        annual_key = (
            np.array([context["apts"][other] + context["adg"][other] * 1e-4 for other in annual_teams])[None, :]
            + eps
            + additions[:, [idx[other] for other in annual_teams]]
        )
        order = annual_key.argsort(1)
        annual_last = np.array(annual_teams)[order[:, 0]]
        annual_second_last = np.array(annual_teams)[order[:, 1]]
        annual_relegated = np.where(annual_last == average_last, annual_second_last, annual_last)
        return (average_last == team) | (annual_relegated == team)

    return np.zeros(n, bool)
