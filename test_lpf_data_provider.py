from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from lpf_data_provider import (
    DATA_PROVIDER_CONTRACT_VERSION,
    CsvProvider,
    CurrentProvider,
    DataProvider,
    ProviderData,
    ProviderError,
    provider_payload,
)
from lpf_services import prepare_competition_snapshot


def _payload():
    teams_a = ["Equipo A", "Equipo B", "Equipo C", "Equipo D"]
    teams_b = ["Equipo E", "Equipo F", "Equipo G", "Equipo H"]
    zones = {
        "A": {team: {"pts": 0, "pj": 0, "dg": 0, "gf": 0, "ga": 0} for team in teams_a},
        "B": {team: {"pts": 0, "pj": 0, "dg": 0, "gf": 0, "ga": 0} for team in teams_b},
    }
    fixture = [
        {"f": 1, "l": "Equipo A", "v": "Equipo B", "tipo": "zona", "zona": "A"},
        {"f": 1, "l": "Equipo C", "v": "Equipo D", "tipo": "zona", "zona": "A"},
        {"f": 1, "l": "Equipo E", "v": "Equipo F", "tipo": "zona", "zona": "B"},
        {"f": 1, "l": "Equipo G", "v": "Equipo H", "tipo": "zona", "zona": "B"},
    ]
    return {
        "zones": zones,
        "fixture": fixture,
        "qualification": {
            "champions": {"apertura": "", "clausura": "", "copa_argentina": ""},
            "international_champions": {"libertadores": "", "sudamericana": ""},
            "copa_argentina_replacement": "",
        },
        "rules": {
            "annual_relegations": 1,
            "average_relegations": 1,
            "opening_rounds": 16,
            "playoff_cutoff": 2,
            "sudamericana_slots": 2,
        },
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_current_provider_emite_payload_json_safe_y_versionado():
    provider = CurrentProvider(_payload())
    assert isinstance(provider, DataProvider)
    data = provider.load()
    assert isinstance(data, ProviderData)
    payload = provider_payload(provider)
    assert payload["data_provider_contract_version"] == DATA_PROVIDER_CONTRACT_VERSION
    assert payload["data_provider"] == "current"
    assert set(payload["zones"]) == {"A", "B"}
    json.dumps(payload, ensure_ascii=False)


def test_current_provider_no_cambia_el_snapshot_del_servicio():
    raw = _payload()
    direct = prepare_competition_snapshot(raw)["result"]
    via_provider = prepare_competition_snapshot(provider_payload(CurrentProvider(raw)))["result"]
    assert via_provider["traceability"]["snapshot_id"] == direct["traceability"]["snapshot_id"]
    for key in direct:
        if key != "traceability":
            assert via_provider[key] == direct[key]


def test_csv_provider_produce_el_mismo_snapshot_que_current_provider(tmp_path):
    raw = _payload()
    for label, key in (("A", "zone_a"), ("B", "zone_b")):
        rows = [
            {
                "equipo": team,
                "pts": row["pts"],
                "pj": row["pj"],
                "dg": row["dg"],
                "gf": row["gf"],
                "ga": row["ga"],
            }
            for team, row in raw["zones"][label].items()
        ]
        _write_csv(tmp_path / f"{key}.csv", rows)

    fixture_rows = [
        {"fecha": row["f"], "local": row["l"], "visitante": row["v"], "tipo": row["tipo"], "zona": row["zona"]}
        for row in raw["fixture"]
    ]
    _write_csv(tmp_path / "fixture.csv", fixture_rows)

    csv_provider = CsvProvider(
        {
            "zone_a": tmp_path / "zone_a.csv",
            "zone_b": tmp_path / "zone_b.csv",
            "fixture": tmp_path / "fixture.csv",
        },
        qualification=raw["qualification"],
        rules=raw["rules"],
    )
    csv_payload = provider_payload(csv_provider)
    assert csv_payload["data_provider"] == "csv"

    current_snapshot = prepare_competition_snapshot(provider_payload(CurrentProvider(raw)))["result"]
    csv_snapshot = prepare_competition_snapshot(csv_payload)["result"]
    assert csv_snapshot["traceability"]["snapshot_id"] == current_snapshot["traceability"]["snapshot_id"]
    for key in current_snapshot:
        if key != "traceability":
            assert csv_snapshot[key] == current_snapshot[key]
    assert current_snapshot["traceability"]["provider"]["name"] == "current"
    assert csv_snapshot["traceability"]["provider"]["name"] == "csv"
    assert csv_snapshot["traceability"]["source"]["updated_at"]


def test_csv_provider_infiere_interzonal_si_no_hay_tipo(tmp_path):
    rows_a = [{"equipo": "Equipo A", "pts": 0, "pj": 0}, {"equipo": "Equipo B", "pts": 0, "pj": 0}]
    rows_b = [{"equipo": "Equipo C", "pts": 0, "pj": 0}, {"equipo": "Equipo D", "pts": 0, "pj": 0}]
    _write_csv(tmp_path / "a.csv", rows_a)
    _write_csv(tmp_path / "b.csv", rows_b)
    _write_csv(tmp_path / "fixture.csv", [{"fecha": 1, "local": "Equipo A", "visitante": "Equipo C"}])
    data = CsvProvider({"zone_a": tmp_path / "a.csv", "zone_b": tmp_path / "b.csv", "fixture": tmp_path / "fixture.csv"}).load()
    assert data.fixture == [{"f": 1, "l": "Equipo A", "v": "Equipo C", "tipo": "inter", "zona": None}]


def test_csv_provider_rechaza_tabla_sin_columnas_minimas(tmp_path):
    _write_csv(tmp_path / "a.csv", [{"club": "Equipo A", "puntos": 1}])
    _write_csv(tmp_path / "b.csv", [{"equipo": "Equipo B", "pts": 1, "pj": 1}])
    with pytest.raises(ProviderError) as exc:
        CsvProvider({"zone_a": tmp_path / "a.csv", "zone_b": tmp_path / "b.csv"}).load()
    assert exc.value.code == "invalid_standings_csv"
    json.dumps(exc.value.to_dict(), ensure_ascii=False)
