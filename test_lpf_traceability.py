from __future__ import annotations

from datetime import datetime, timezone

import pytest

from lpf_data_provider import CurrentProvider, provider_payload
from lpf_services import ContractError, prepare_competition_snapshot, validate_competition_snapshot
from lpf_snapshot import snapshot_traceability_summary


def _payload():
    zones = {
        "A": {
            "Equipo A": {"pts": 3, "pj": 1, "dg": 1, "gf": 1, "ga": 0},
            "Equipo B": {"pts": 0, "pj": 1, "dg": -1, "gf": 0, "ga": 1},
        },
        "B": {
            "Equipo C": {"pts": 0, "pj": 0, "dg": 0, "gf": 0, "ga": 0},
            "Equipo D": {"pts": 0, "pj": 0, "dg": 0, "gf": 0, "ga": 0},
        },
    }
    return {
        "zones": zones,
        "played": [{"home": "Equipo A", "away": "Equipo B", "home_goals": 1, "away_goals": 0}],
        "fixture": [
            {"f": 1, "l": "Equipo A", "v": "Equipo B", "tipo": "zona", "zona": "A"},
            {"f": 2, "l": "Equipo C", "v": "Equipo D", "tipo": "zona", "zona": "B"},
        ],
        "rules": {"opening_rounds": 16, "playoff_cutoff": 1, "sudamericana_slots": 1},
        "provenance": {
            "source_name": "Proveedor de prueba",
            "source_updated_at": "2026-08-13T12:00:00+00:00",
            "data_as_of": "2026-08-13T12:00:00+00:00",
            "sources": ["tabla", "resultados"],
            "warnings": [],
        },
    }


def test_snapshot_traceability_records_source_coverage_and_quality():
    snapshot = prepare_competition_snapshot(provider_payload(CurrentProvider(_payload())))["result"]
    trace = snapshot["traceability"]
    assert snapshot["snapshot_schema_version"] == "3"
    assert trace["traceability_version"] == "1"
    assert trace["provider"] == {"name": "current", "contract_version": "2"}
    assert trace["source"]["name"] == "Proveedor de prueba"
    assert trace["source"]["updated_at"] == "2026-08-13T12:00:00+00:00"
    assert trace["coverage"]["played_match_count"] == 1
    assert trace["coverage"]["last_confirmed_round"] == 1
    assert trace["coverage"]["frontier_played_matches"] == [
        {"round": 1, "home": "Equipo A", "away": "Equipo B"}
    ]
    assert trace["coverage"]["fixture_through_round"] == 2
    assert trace["snapshot_id"]


def test_snapshot_id_is_independent_of_provider_provenance():
    first = provider_payload(CurrentProvider(_payload()))
    second_raw = _payload()
    second_raw["provenance"] = {
        "source_name": "Otra fuente",
        "source_updated_at": "2026-08-13T13:00:00+00:00",
        "sources": ["otra"],
        "warnings": ["aviso"],
    }
    second = provider_payload(CurrentProvider(second_raw))
    snap_a = prepare_competition_snapshot(first)["result"]
    snap_b = prepare_competition_snapshot(second)["result"]
    assert snap_a["traceability"]["snapshot_id"] == snap_b["traceability"]["snapshot_id"]


def test_traceability_summary_calculates_age_without_mutating_snapshot():
    snapshot = prepare_competition_snapshot(provider_payload(CurrentProvider(_payload())))["result"]
    summary = snapshot_traceability_summary(
        snapshot,
        now=datetime(2026, 8, 13, 14, 0, tzinfo=timezone.utc),
    )
    assert summary["available"] is True
    assert summary["timestamp_known"] is True
    assert summary["age_hours"] == 2.0


def test_schema_2_without_traceability_remains_accepted_for_compatibility():
    snapshot = prepare_competition_snapshot(provider_payload(CurrentProvider(_payload())))["result"]
    snapshot["snapshot_schema_version"] = "2"
    snapshot.pop("traceability", None)
    validated = validate_competition_snapshot({"snapshot": snapshot})["result"]
    assert validated["snapshot_schema_version"] == "2"
    assert validated["has_traceability"] is False


def test_schema_3_requires_traceability():
    snapshot = prepare_competition_snapshot(provider_payload(CurrentProvider(_payload())))["result"]
    snapshot.pop("traceability", None)
    with pytest.raises(ContractError) as exc:
        validate_competition_snapshot({"snapshot": snapshot})
    assert exc.value.code == "invalid_snapshot"
    assert exc.value.field == "snapshot.traceability"
