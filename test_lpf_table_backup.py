"""Pruebas del respaldo persistente de tablas LPF, sin Streamlit."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from lpf_data_2026 import TABLA_ANUAL_LPF_2026, ZONA_A_LPF_2026, ZONA_B_LPF_2026
from lpf_parsers import parse_tabla_anual
from lpf_table_backup import (
    build_table_backup,
    load_table_backup,
    select_valid_table_backup,
    table_backup_candidates,
    write_table_backup,
)


def _bases():
    zones = {
        "A": parse_tabla_anual(ZONA_A_LPF_2026)[0],
        "B": parse_tabla_anual(ZONA_B_LPF_2026)[0],
    }
    annual = parse_tabla_anual(TABLA_ANUAL_LPF_2026)[0]
    return zones, annual


def test_build_backup_es_json_safe_y_preserva_tablas():
    zones, annual = _bases()
    stamp = "2026-08-11T12:00:00+00:00"
    payload = build_table_backup(zones, annual, "ESPN + FA", updated_at=stamp)

    assert payload["schema"] == 1
    assert payload["competition"] == "LPF Clausura 2026"
    assert payload["source"] == "ESPN + FA"
    assert payload["updated_at"] == stamp
    assert set(payload["zones"]) == {"A", "B"}
    assert payload["annual"]
    json.dumps(payload, ensure_ascii=False)


def test_write_y_load_desde_disco_sin_streamlit(tmp_path):
    zones, annual = _bases()
    now = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)
    payload = build_table_backup(
        zones, annual, "archivo de prueba", updated_at=(now - timedelta(hours=3)).isoformat()
    )
    path = tmp_path / "last_valid.json"
    write_table_backup(payload, path)

    loaded = load_table_backup(path=path, now=now)
    assert loaded[0] == zones
    assert loaded[1] == annual
    assert loaded[2] == "archivo de prueba"
    assert loaded[3] == 3.0
    assert loaded[4] is None
    assert not path.with_suffix(".json.tmp").exists()


def test_sesion_tiene_prioridad_sobre_disco(tmp_path):
    zones, annual = _bases()
    now = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)
    session_payload = build_table_backup(
        zones, annual, "sesión", updated_at=(now - timedelta(hours=1)).isoformat()
    )
    disk_payload = build_table_backup(
        zones, annual, "disco", updated_at=(now - timedelta(minutes=5)).isoformat()
    )
    path = tmp_path / "last_valid.json"
    write_table_backup(disk_payload, path)

    candidates = table_backup_candidates(session_payload=session_payload, path=path)
    assert [location for location, _ in candidates] == ["sesión", "disco"]
    loaded = select_valid_table_backup(candidates, now=now)
    assert loaded[2] == "sesión"
    assert loaded[3] == 1.0


def test_si_sesion_esta_vencida_cae_al_disco_valido(tmp_path):
    zones, annual = _bases()
    now = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)
    session_payload = build_table_backup(
        zones, annual, "sesión vieja", updated_at=(now - timedelta(days=9)).isoformat()
    )
    disk_payload = build_table_backup(
        zones, annual, "disco vigente", updated_at=(now - timedelta(hours=2)).isoformat()
    )
    path = tmp_path / "last_valid.json"
    write_table_backup(disk_payload, path)

    loaded = load_table_backup(session_payload=session_payload, path=path, now=now)
    assert loaded[0] == zones
    assert loaded[1] == annual
    assert loaded[2] == "disco vigente"
    assert loaded[3] == 2.0
    assert loaded[4] is None


def test_acepta_formato_legacy_con_zonas_en_la_raiz():
    zones, annual = _bases()
    now = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)
    payload = {
        "updated_at": now.isoformat(),
        "source": "legacy",
        "Zona A": zones["A"],
        "zone_b": zones["B"],
        "tabla_anual": annual,
    }

    loaded = select_valid_table_backup([("sesión", payload)], now=now)
    assert loaded[0] == zones
    assert loaded[1] == annual
    assert loaded[2] == "legacy"
    assert loaded[4] is None


def test_reporta_respaldo_vencido_con_mismo_formato_editorial():
    zones, annual = _bases()
    now = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)
    payload = build_table_backup(
        zones, annual, "viejo", updated_at=(now - timedelta(days=8)).isoformat()
    )

    loaded = select_valid_table_backup([("sesión", payload)], max_age_hours=168, now=now)
    assert loaded[:4] == ({}, {}, "", None)
    assert loaded[4] == "respaldo de sesión demasiado viejo (8 días)"


def test_json_invalido_en_disco_no_bloquea_candidato_de_sesion(tmp_path):
    zones, annual = _bases()
    now = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)
    session_payload = build_table_backup(zones, annual, "sesión", updated_at=now.isoformat())
    path = tmp_path / "last_valid.json"
    path.write_text("{no-es-json", encoding="utf-8")

    loaded = load_table_backup(session_payload=session_payload, path=path, now=now)
    assert loaded[0] == zones
    assert loaded[1] == annual
    assert loaded[2] == "sesión"
    assert loaded[4] is None


def test_modulo_no_depende_de_streamlit_ni_red():
    import lpf_table_backup

    source = open(lpf_table_backup.__file__, encoding="utf-8").read()
    assert "import streamlit" not in source
    assert "import requests" not in source
