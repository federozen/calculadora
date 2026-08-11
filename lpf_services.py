"""Fachada pura y JSON-safe para exponer cálculos LPF.

Este módulo no es una API HTTP. Es la frontera de aplicación que una API futura
puede invocar sin importar Streamlit, requests ni detalles de proveedores. Recibe
diccionarios/listas compatibles con JSON, valida lo mínimo necesario y delega toda
la matemática en los motores existentes.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass

from lpf_pisos import piso_por_corte
from lpf_scenarios import point_ladder, scenario_rank_bounds
from lpf_standings import DEFAULT_CRITERIOS, _orden
from lpf_version import __version__

CONTRACT_VERSION = "1"


class ContractError(ValueError):
    """Error de entrada estable para que una interfaz pueda mapearlo a su protocolo."""

    def __init__(self, code: str, message: str, *, field: str | None = None):
        super().__init__(message)
        self.code = str(code)
        self.field = field

    def to_dict(self) -> dict[str, object]:
        out: dict[str, object] = {"code": self.code, "message": str(self)}
        if self.field:
            out["field"] = self.field
        return out


def _envelope(calculation: str, result: object) -> dict[str, object]:
    return {
        "contract_version": CONTRACT_VERSION,
        "calculation_version": __version__,
        "calculation": calculation,
        "result": _json_safe(result),
    }


def _json_safe(value: object) -> object:
    """Convierte dataclasses/tuplas/set en estructuras serializables por ``json``."""
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


def _mapping(payload: object) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ContractError("invalid_payload", "El payload debe ser un objeto JSON.")
    return payload


def _required_text(payload: Mapping[str, object], field: str) -> str:
    value = str(payload.get(field, "") or "").strip()
    if not value:
        raise ContractError("missing_field", f"Falta el campo obligatorio '{field}'.", field=field)
    return value


def _required_int(payload: Mapping[str, object], field: str) -> int:
    if field not in payload:
        raise ContractError("missing_field", f"Falta el campo obligatorio '{field}'.", field=field)
    try:
        return int(payload[field])
    except (TypeError, ValueError) as exc:
        raise ContractError("invalid_integer", f"'{field}' debe ser un entero.", field=field) from exc


def _teams(payload: Mapping[str, object]) -> list[str]:
    raw = payload.get("teams")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ContractError("invalid_teams", "'teams' debe ser una lista de equipos.", field="teams")
    teams = [str(team).strip() for team in raw]
    if not teams or any(not team for team in teams):
        raise ContractError("invalid_teams", "'teams' no puede estar vacío ni contener nombres vacíos.", field="teams")
    if len(set(teams)) != len(teams):
        raise ContractError("duplicate_team", "'teams' contiene equipos repetidos.", field="teams")
    return teams


def _played_matches(raw: object) -> list[tuple[str, str, int, int]]:
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ContractError("invalid_matches", "'matches' debe ser una lista.", field="matches")
    out: list[tuple[str, str, int, int]] = []
    for index, row in enumerate(raw):
        try:
            if isinstance(row, Mapping):
                home = str(row["home"]).strip()
                away = str(row["away"]).strip()
                hg = int(row["home_goals"])
                ag = int(row["away_goals"])
            else:
                home, away, hg, ag = row  # type: ignore[misc]
                home, away, hg, ag = str(home).strip(), str(away).strip(), int(hg), int(ag)
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(
                "invalid_match",
                f"Partido inválido en matches[{index}].",
                field="matches",
            ) from exc
        if not home or not away or home == away or hg < 0 or ag < 0:
            raise ContractError(
                "invalid_match",
                f"Partido inválido en matches[{index}].",
                field="matches",
            )
        out.append((home, away, hg, ag))
    return out


def _fixture_pairs(raw: object) -> list[tuple[str, str]]:
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ContractError("invalid_matches", "'matches' debe ser una lista.", field="matches")
    out: list[tuple[str, str]] = []
    for index, row in enumerate(raw):
        try:
            if isinstance(row, Mapping):
                home = str(row["home"]).strip()
                away = str(row["away"]).strip()
            else:
                home, away = row  # type: ignore[misc]
                home, away = str(home).strip(), str(away).strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(
                "invalid_match",
                f"Partido inválido en matches[{index}].",
                field="matches",
            ) from exc
        if not home or not away or home == away:
            raise ContractError(
                "invalid_match",
                f"Partido inválido en matches[{index}].",
                field="matches",
            )
        out.append((home, away))
    return out


def _fixed_results(raw: object) -> dict[tuple[str, str], str]:
    if raw is None:
        return {}
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ContractError("invalid_fixed", "'fixed' debe ser una lista.", field="fixed")
    out: dict[tuple[str, str], str] = {}
    for index, row in enumerate(raw):
        if not isinstance(row, Mapping):
            raise ContractError("invalid_fixed", f"Resultado inválido en fixed[{index}].", field="fixed")
        home = str(row.get("home", "")).strip()
        away = str(row.get("away", "")).strip()
        result = str(row.get("result", "")).upper().strip()
        if not home or not away or home == away or result not in {"L", "E", "V"}:
            raise ContractError("invalid_fixed", f"Resultado inválido en fixed[{index}].", field="fixed")
        out[(home, away)] = result
    return out


def calculate_standings(payload: Mapping[str, object]) -> dict[str, object]:
    """Calcula posiciones y tabla desde un payload JSON-compatible."""
    payload = _mapping(payload)
    teams = _teams(payload)
    matches = _played_matches(payload.get("matches"))
    unknown = sorted({team for row in matches for team in row[:2]} - set(teams))
    if unknown:
        raise ContractError(
            "unknown_team",
            f"Hay equipos de partidos que no figuran en 'teams': {', '.join(unknown)}.",
            field="matches",
        )

    criteria_raw = payload.get("tiebreakers")
    if criteria_raw is None:
        criteria = DEFAULT_CRITERIOS
    elif isinstance(criteria_raw, Sequence) and not isinstance(criteria_raw, (str, bytes)):
        criteria = tuple(str(item) for item in criteria_raw)
    else:
        raise ContractError("invalid_tiebreakers", "'tiebreakers' debe ser una lista.", field="tiebreakers")

    fair_play = payload.get("fair_play")
    ranking = payload.get("ranking")
    if fair_play is not None and not isinstance(fair_play, Mapping):
        raise ContractError("invalid_fair_play", "'fair_play' debe ser un objeto.", field="fair_play")
    if ranking is not None and not isinstance(ranking, Mapping):
        raise ContractError("invalid_ranking", "'ranking' debe ser un objeto.", field="ranking")

    order, stats = _orden(
        teams,
        matches,
        fair_play=fair_play,
        ranking=ranking,
        criterios=criteria,
    )
    table = [
        {
            "position": position,
            "team": team,
            "played": int(stats[team]["pj"]),
            "points": int(stats[team]["pts"]),
            "goals_for": int(stats[team]["gf"]),
            "goals_against": int(stats[team]["ga"]),
            "goal_difference": int(stats[team]["dg"]),
        }
        for position, team in enumerate(order, 1)
    ]
    return _envelope(
        "standings",
        {
            "positions": {team: position for position, team in enumerate(order, 1)},
            "table": table,
            "tiebreakers": list(criteria),
        },
    )


def calculate_point_ladder(payload: Mapping[str, object]) -> dict[str, object]:
    """Expone la escalera exacta de puntos sin filtrar objetos de dominio."""
    payload = _mapping(payload)
    base = payload.get("base")
    if not isinstance(base, Mapping) or not base:
        raise ContractError("invalid_base", "'base' debe ser un objeto no vacío.", field="base")
    team = _required_text(payload, "team")
    if team not in base:
        raise ContractError("unknown_team", f"'{team}' no está en 'base'.", field="team")
    cutoff = _required_int(payload, "cutoff")
    matches = _fixture_pairs(payload.get("matches"))
    result = point_ladder(base, matches, team, cutoff)
    return _envelope("point_ladder", result)


def calculate_rank_window(payload: Mapping[str, object]) -> dict[str, object]:
    """Expone el rango exacto de puesto para una ventana y resultados fijados."""
    payload = _mapping(payload)
    base = payload.get("base")
    if not isinstance(base, Mapping) or not base:
        raise ContractError("invalid_base", "'base' debe ser un objeto no vacío.", field="base")
    team = _required_text(payload, "team")
    if team not in base:
        raise ContractError("unknown_team", f"'{team}' no está en 'base'.", field="team")
    matches = _fixture_pairs(payload.get("matches"))
    fixed = _fixed_results(payload.get("fixed"))
    result = scenario_rank_bounds(base, matches, team, fixed)
    return _envelope("rank_window", result)


def calculate_objective_floor(payload: Mapping[str, object]) -> dict[str, object]:
    """Expone los puntos necesarios para quedar dentro de un corte de tabla."""
    payload = _mapping(payload)
    base = payload.get("base")
    rest = payload.get("remaining")
    if not isinstance(base, Mapping) or not base:
        raise ContractError("invalid_base", "'base' debe ser un objeto no vacío.", field="base")
    if not isinstance(rest, Mapping):
        raise ContractError("invalid_remaining", "'remaining' debe ser un objeto.", field="remaining")
    team = _required_text(payload, "team")
    cutoff = _required_int(payload, "cutoff")
    key = str(payload.get("objective_key", "objective") or "objective")
    name = str(payload.get("objective_name", "el objetivo") or "el objetivo")
    matches = _fixture_pairs(payload.get("matches"))

    floor = piso_por_corte(base, rest, matches, team, cutoff, clave=key, nombre=name)
    result = asdict(floor)
    result["minimum_possible"] = floor.minimo_posible
    result["exact_guarantee"] = floor.garantia_exacta
    result["conservative_reference"] = floor.referencia_conservadora
    result["safe_value"] = floor.piso
    result["floor"] = floor.piso  # alias legado del contrato v1
    result["reading"] = floor.lectura()
    return _envelope("objective_floor", result)
