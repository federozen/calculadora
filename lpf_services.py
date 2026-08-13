"""Fachada pura y JSON-safe para exponer cálculos LPF.

Este módulo no es una API HTTP. Es la frontera de aplicación que una API futura
puede invocar sin importar Streamlit, requests ni detalles de proveedores. Recibe
diccionarios/listas compatibles con JSON, valida lo mínimo necesario y delega toda
la matemática en los motores existentes.
"""
from __future__ import annotations

LPF_RUNTIME_API = 15


from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass

from lpf_pisos import VENTANA_EXACTA, piso_no_descenso, piso_por_corte
from lpf_scenarios import point_ladder, scenario_rank_bounds
from lpf_snapshot import (
    SNAPSHOT_SCHEMA_VERSION,
    build_competition_snapshot,
    snapshot_average_totals,
    snapshot_scope,
)
from lpf_standings import DEFAULT_CRITERIOS, _orden
from lpf_version import __version__

CONTRACT_VERSION = "1"
SUPPORTED_QUERY_TYPES = ("objective_points", "point_ladder", "rank_window", "descent_points")


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



def _floor_exact_guarantee(floor: object) -> int | None:
    """Tolera objetos PisoObjetivo de contratos internos anteriores a 3.8.8."""
    try:
        return getattr(floor, "garantia_exacta")
    except AttributeError:
        if bool(getattr(floor, "exacto", False)):
            return getattr(floor, "piso_exacto", None)
        return None


def _floor_conservative_reference(floor: object) -> int | None:
    """Tolera objetos PisoObjetivo de contratos internos anteriores a 3.8.8."""
    try:
        return getattr(floor, "referencia_conservadora")
    except AttributeError:
        if bool(getattr(floor, "exacto", False)):
            return None
        value = getattr(floor, "piso_conservador", None)
        return value if value is not None else getattr(floor, "piso_exacto", None)

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
    result["minimum_guarantee"] = _floor_exact_guarantee(floor)
    result["safe_total"] = floor.piso
    # Alias técnicos del contrato v1: se conservan para no romper consumidores.
    result["exact_guarantee"] = result["minimum_guarantee"]
    result["conservative_reference"] = _floor_conservative_reference(floor)
    result["safe_value"] = result["safe_total"]
    result["floor"] = floor.piso  # alias legado del contrato v1
    result["reading"] = floor.lectura()
    return _envelope("objective_floor", result)



def service_capabilities() -> dict[str, object]:
    """Describe el contrato disponible sin depender de Streamlit ni de HTTP."""
    return _envelope(
        "capabilities",
        {
            "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
            "batch_query_types": list(SUPPORTED_QUERY_TYPES),
            "operations": [
                "standings",
                "point_ladder",
                "rank_window",
                "objective_floor",
                "competition_snapshot",
                "validate_snapshot",
                "competition_batch",
            ],
            "exact_window_remaining_matches": VENTANA_EXACTA,
        },
    )


def _unwrap_snapshot(raw: object) -> Mapping[str, object]:
    """Acepta una foto cruda o el sobre completo devuelto por el servicio."""
    if not isinstance(raw, Mapping):
        raise ContractError("invalid_snapshot", "'snapshot' debe ser un objeto.", field="snapshot")
    if {"contract_version", "calculation", "result"}.issubset(raw):
        if str(raw.get("calculation", "")) != "competition_snapshot":
            raise ContractError(
                "invalid_snapshot_envelope",
                "El sobre informado no corresponde a 'competition_snapshot'.",
                field="snapshot.calculation",
            )
        result = raw.get("result")
        if not isinstance(result, Mapping):
            raise ContractError(
                "invalid_snapshot_envelope",
                "El resultado del snapshot debe ser un objeto.",
                field="snapshot.result",
            )
        return result
    return raw


def _snapshot_int_mapping(raw: object, field: str) -> dict[str, int]:
    if not isinstance(raw, Mapping):
        raise ContractError("invalid_snapshot", f"'{field}' debe ser un objeto.", field=field)
    out: dict[str, int] = {}
    for team, value in raw.items():
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ContractError(
                "invalid_snapshot", f"'{field}.{team}' debe ser un entero.", field=f"{field}.{team}"
            ) from exc
        if number < 0:
            raise ContractError(
                "invalid_snapshot", f"'{field}.{team}' no puede ser negativo.", field=f"{field}.{team}"
            )
        out[str(team)] = number
    return out


def _validate_snapshot(snapshot: Mapping[str, object], *, require_canonical: bool) -> dict[str, object]:
    """Valida forma e invariantes simples; no ejecuta matemática de competencia."""
    schema = snapshot.get("snapshot_schema_version")
    if schema is not None and str(schema) != SNAPSHOT_SCHEMA_VERSION:
        raise ContractError(
            "unsupported_snapshot_schema",
            f"Snapshot schema no soportado: '{schema}'. Se espera '{SNAPSHOT_SCHEMA_VERSION}'.",
            field="snapshot.snapshot_schema_version",
        )

    teams_raw = snapshot.get("teams")
    if require_canonical and teams_raw is None:
        raise ContractError(
            "invalid_snapshot", "Falta 'teams' en la foto canónica.", field="snapshot.teams"
        )
    teams: list[str] = []
    if teams_raw is not None:
        if not isinstance(teams_raw, Sequence) or isinstance(teams_raw, (str, bytes)):
            raise ContractError("invalid_snapshot", "'snapshot.teams' debe ser una lista.", field="snapshot.teams")
        teams = [str(team).strip() for team in teams_raw]
        if not teams or any(not team for team in teams) or len(set(teams)) != len(teams):
            raise ContractError(
                "invalid_snapshot",
                "'snapshot.teams' debe contener equipos únicos y no vacíos.",
                field="snapshot.teams",
            )

    zones = snapshot.get("zones")
    if require_canonical and (not isinstance(zones, Mapping) or not zones):
        raise ContractError("invalid_snapshot", "Falta 'zones' en la foto canónica.", field="snapshot.zones")
    zone_teams: set[str] = set()
    if zones is not None:
        if not isinstance(zones, Mapping):
            raise ContractError("invalid_snapshot", "'snapshot.zones' debe ser un objeto.", field="snapshot.zones")
        for label, base in zones.items():
            if not isinstance(base, Mapping):
                raise ContractError(
                    "invalid_snapshot", f"La zona '{label}' debe ser un objeto.", field=f"snapshot.zones.{label}"
                )
            for team, row in base.items():
                if not isinstance(row, Mapping):
                    raise ContractError(
                        "invalid_snapshot",
                        f"La fila de '{team}' en la zona '{label}' debe ser un objeto.",
                        field=f"snapshot.zones.{label}.{team}",
                    )
                if str(team) in zone_teams:
                    raise ContractError(
                        "invalid_snapshot",
                        f"'{team}' aparece en más de una zona.",
                        field="snapshot.zones",
                    )
                zone_teams.add(str(team))

    if teams and zone_teams and set(teams) != zone_teams:
        missing = sorted(set(teams) - zone_teams)
        extra = sorted(zone_teams - set(teams))
        detail = []
        if missing:
            detail.append("sin zona: " + ", ".join(missing))
        if extra:
            detail.append("fuera de teams: " + ", ".join(extra))
        raise ContractError(
            "inconsistent_snapshot",
            "La nómina de equipos y las zonas no coinciden (" + "; ".join(detail) + ").",
            field="snapshot.zones",
        )

    remaining = _snapshot_int_mapping(snapshot.get("remaining"), "snapshot.remaining")
    if teams and set(remaining) != set(teams):
        raise ContractError(
            "inconsistent_snapshot",
            "'snapshot.remaining' debe contener exactamente los equipos de 'snapshot.teams'.",
            field="snapshot.remaining",
        )

    pending_raw = snapshot.get("pending")
    if not isinstance(pending_raw, Sequence) or isinstance(pending_raw, (str, bytes)):
        raise ContractError("invalid_snapshot", "'snapshot.pending' debe ser una lista.", field="snapshot.pending")
    pending_counts = {team: 0 for team in teams}
    pending_count = 0
    known = set(teams) if teams else (set(remaining) | zone_teams)
    for index, row in enumerate(pending_raw):
        if not isinstance(row, Mapping):
            raise ContractError(
                "invalid_snapshot", f"Partido inválido en pending[{index}].", field=f"snapshot.pending[{index}]"
            )
        home = str(row.get("home", "") or "").strip()
        away = str(row.get("away", "") or "").strip()
        if not home or not away or home == away:
            raise ContractError(
                "invalid_snapshot", f"Partido inválido en pending[{index}].", field=f"snapshot.pending[{index}]"
            )
        if known and (home not in known or away not in known):
            raise ContractError(
                "inconsistent_snapshot",
                f"pending[{index}] contiene un equipo fuera de la foto.",
                field=f"snapshot.pending[{index}]",
            )
        if teams:
            pending_counts[home] += 1
            pending_counts[away] += 1
        pending_count += 1

    if teams and pending_counts != remaining:
        different = [team for team in teams if pending_counts.get(team, 0) != remaining.get(team, 0)]
        sample = ", ".join(different[:5])
        suffix = "…" if len(different) > 5 else ""
        raise ContractError(
            "inconsistent_snapshot",
            "Los partidos pendientes no coinciden con 'remaining' para: " + sample + suffix + ".",
            field="snapshot.remaining",
        )

    rules = snapshot.get("rules")
    if rules is not None:
        if not isinstance(rules, Mapping):
            raise ContractError("invalid_snapshot", "'snapshot.rules' debe ser un objeto.", field="snapshot.rules")
        for key in ("annual_relegations", "average_relegations"):
            if key in rules:
                try:
                    value = int(rules[key])
                except (TypeError, ValueError) as exc:
                    raise ContractError(
                        "invalid_snapshot", f"'snapshot.rules.{key}' debe ser entero.", field=f"snapshot.rules.{key}"
                    ) from exc
                if value < 0:
                    raise ContractError(
                        "invalid_snapshot", f"'snapshot.rules.{key}' no puede ser negativo.", field=f"snapshot.rules.{key}"
                    )

    return {
        "snapshot_schema_version": str(schema or SNAPSHOT_SCHEMA_VERSION),
        "canonical": bool(teams and zone_teams),
        "team_count": len(teams) if teams else len(known),
        "zone_count": len(zones) if isinstance(zones, Mapping) else 0,
        "pending_match_count": pending_count,
        "has_annual": isinstance(snapshot.get("annual"), Mapping) and bool(snapshot.get("annual")),
        "has_average_history": isinstance(snapshot.get("previous_averages"), Mapping) and bool(snapshot.get("previous_averages")),
    }


def validate_competition_snapshot(payload: Mapping[str, object]) -> dict[str, object]:
    """Valida una foto canónica antes de enviarla a cálculos batch."""
    payload = _mapping(payload)
    snapshot = _unwrap_snapshot(payload.get("snapshot"))
    summary = _validate_snapshot(snapshot, require_canonical=True)
    return _envelope("validate_snapshot", summary)


def _optional_mapping(payload: Mapping[str, object], field: str) -> Mapping[str, object] | None:
    raw = payload.get(field)
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ContractError("invalid_mapping", f"'{field}' debe ser un objeto.", field=field)
    return raw


def _zones_mapping(payload: Mapping[str, object]) -> Mapping[str, Mapping[str, Mapping[str, object]]]:
    raw = payload.get("zones")
    if not isinstance(raw, Mapping) or not raw:
        raise ContractError("invalid_zones", "'zones' debe ser un objeto no vacío.", field="zones")
    for label, base in raw.items():
        if not isinstance(base, Mapping):
            raise ContractError("invalid_zone", f"La zona '{label}' debe ser un objeto.", field="zones")
        for team, row in base.items():
            if not isinstance(row, Mapping):
                raise ContractError(
                    "invalid_zone_row",
                    f"La fila de '{team}' en la zona '{label}' debe ser un objeto.",
                    field="zones",
                )
    return raw  # type: ignore[return-value]


def _fixture_payload(raw: object) -> list[Mapping[str, object]]:
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ContractError("invalid_fixture", "'fixture' debe ser una lista.", field="fixture")
    out: list[Mapping[str, object]] = []
    for index, row in enumerate(raw):
        if not isinstance(row, Mapping):
            raise ContractError(
                "invalid_fixture",
                f"Partido inválido en fixture[{index}].",
                field="fixture",
            )
        if not str(row.get("l", "")).strip() or not str(row.get("v", "")).strip():
            raise ContractError(
                "invalid_fixture",
                f"Partido inválido en fixture[{index}].",
                field="fixture",
            )
        out.append(row)
    return out


def prepare_competition_snapshot(payload: Mapping[str, object]) -> dict[str, object]:
    """Construye una foto completa y JSON-safe usando el estado canónico de la app."""
    payload = _mapping(payload)
    zones = _zones_mapping(payload)
    played = _played_matches(payload.get("played"))
    annual = _optional_mapping(payload, "annual")
    opening = _optional_mapping(payload, "opening")
    previous = _optional_mapping(payload, "previous_averages")
    fixture = _fixture_payload(payload.get("fixture"))
    rules = payload.get("rules") or {}
    if not isinstance(rules, Mapping):
        raise ContractError("invalid_rules", "'rules' debe ser un objeto.", field="rules")
    try:
        annual_relegations = int(rules.get("annual_relegations", 1))
        average_relegations = int(rules.get("average_relegations", 1))
    except (TypeError, ValueError) as exc:
        raise ContractError("invalid_rules", "Las reglas de descenso deben ser enteras.", field="rules") from exc

    snapshot, report = build_competition_snapshot(
        zones,
        played=played,
        annual=annual,  # type: ignore[arg-type]
        opening=opening,  # type: ignore[arg-type]
        previous_averages=previous,
        fixture=fixture,
        annual_relegations=annual_relegations,
        average_relegations=average_relegations,
    )
    snapshot["audit"] = report
    return _envelope("competition_snapshot", snapshot)


def _snapshot_query_scope(
    snapshot: Mapping[str, object],
    query: Mapping[str, object],
) -> tuple[Mapping[str, object], Mapping[str, int], list[tuple[str, str]]]:
    scope = str(query.get("scope", "zone") or "zone").strip().lower()
    zone = str(query.get("zone", "") or "").strip() or None
    try:
        return snapshot_scope(snapshot, scope, zone=zone)
    except ValueError as exc:
        field = "zone" if scope == "zone" else "scope"
        raise ContractError("invalid_scope", str(exc), field=field) from exc


def _objective_result(floor: object) -> dict[str, object]:
    result = asdict(floor)  # type: ignore[arg-type]
    result["minimum_possible"] = floor.minimo_posible  # type: ignore[attr-defined]
    result["minimum_guarantee"] = _floor_exact_guarantee(floor)  # type: ignore[attr-defined]
    result["safe_total"] = floor.piso  # type: ignore[attr-defined]
    # Alias técnicos del contrato v1: se conservan para no romper consumidores.
    result["exact_guarantee"] = result["minimum_guarantee"]
    result["conservative_reference"] = _floor_conservative_reference(floor)  # type: ignore[attr-defined]
    result["safe_value"] = result["safe_total"]
    result["reading"] = floor.lectura()  # type: ignore[attr-defined]
    return result


def calculate_competition_batch(payload: Mapping[str, object]) -> dict[str, object]:
    """Ejecuta varias consultas sobre una misma foto canónica sin recalcular la carga."""
    payload = _mapping(payload)
    snapshot = _unwrap_snapshot(payload.get("snapshot"))
    _validate_snapshot(snapshot, require_canonical=False)
    queries = payload.get("queries")
    if not isinstance(queries, Sequence) or isinstance(queries, (str, bytes)) or not queries:
        raise ContractError("invalid_queries", "'queries' debe ser una lista no vacía.", field="queries")

    outputs: list[dict[str, object]] = []
    for index, raw_query in enumerate(queries):
        if not isinstance(raw_query, Mapping):
            raise ContractError("invalid_query", f"Consulta inválida en queries[{index}].", field="queries")
        qtype = str(raw_query.get("type", "") or "").strip().lower()
        query_id = str(raw_query.get("id", index))
        team = str(raw_query.get("team", "") or "").strip()

        if qtype in {"objective_points", "point_ladder", "rank_window"}:
            base, remaining, matches = _snapshot_query_scope(snapshot, raw_query)
            if not team:
                raise ContractError("missing_field", "Falta el campo obligatorio 'team'.", field="team")
            if team not in base:
                raise ContractError("unknown_team", f"'{team}' no está en el alcance elegido.", field="team")

        if qtype == "objective_points":
            cutoff = _required_int(raw_query, "cutoff")
            floor = piso_por_corte(
                base,
                remaining,
                matches,
                team,
                cutoff,
                clave=str(raw_query.get("objective_key", "objective") or "objective"),
                nombre=str(raw_query.get("objective_name", "el objetivo") or "el objetivo"),
            )
            result = _objective_result(floor)

        elif qtype == "point_ladder":
            cutoff = _required_int(raw_query, "cutoff")
            result = point_ladder(base, matches, team, cutoff)

        elif qtype == "rank_window":
            fixed = _fixed_results(raw_query.get("fixed"))
            result = scenario_rank_bounds(base, matches, team, fixed)

        elif qtype == "descent_points":
            annual = snapshot.get("annual")
            remaining = snapshot.get("remaining")
            pending = snapshot.get("pending")
            rules = snapshot.get("rules") or {}
            if not isinstance(annual, Mapping) or not isinstance(remaining, Mapping) or not isinstance(pending, Sequence):
                raise ContractError("invalid_snapshot", "El snapshot no tiene datos completos de descenso.", field="snapshot")
            if not team:
                raise ContractError("missing_field", "Falta el campo obligatorio 'team'.", field="team")
            if team not in annual:
                raise ContractError("unknown_team", f"'{team}' no está en la Tabla Anual.", field="team")
            matches = _fixture_pairs(pending)
            prom_totals = snapshot_average_totals(snapshot)
            annual_relegations = int(rules.get("annual_relegations", 1)) if isinstance(rules, Mapping) else 1
            average_relegations = int(rules.get("average_relegations", 1)) if isinstance(rules, Mapping) else 1
            floor = piso_no_descenso(
                annual,
                remaining,
                matches,
                team,
                n_anual=annual_relegations,
                prom_totales=prom_totals,
                n_prom=average_relegations,
            )
            result = _objective_result(floor)

        else:
            raise ContractError(
                "unknown_query",
                f"Tipo de consulta no soportado: '{qtype}'.",
                field="type",
            )

        outputs.append({"id": query_id, "type": qtype, "result": result})

    return _envelope(
        "competition_batch",
        {
            "snapshot_schema_version": str(snapshot.get("snapshot_schema_version") or SNAPSHOT_SCHEMA_VERSION),
            "query_count": len(outputs),
            "queries": outputs,
        },
    )
