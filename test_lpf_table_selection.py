"""Pruebas de la política pura de selección de tablas LPF."""
from copy import deepcopy

from lpf_data_2026 import TABLA_ANUAL_LPF_2026, ZONA_A_LPF_2026, ZONA_B_LPF_2026
from lpf_parsers import parse_tabla_anual
from lpf_table_selection import select_lpf_tables


def _bases():
    zones = {
        "A": parse_tabla_anual(ZONA_A_LPF_2026)[0],
        "B": parse_tabla_anual(ZONA_B_LPF_2026)[0],
    }
    annual = parse_tabla_anual(TABLA_ANUAL_LPF_2026)[0]
    return zones, annual


def test_prioriza_espn_para_zonas_y_fa_para_anual():
    zones, annual = _bases()
    result = select_lpf_tables(espn_zones=zones, fa_zones=zones, fa_annual=annual)

    assert result["zones"] == zones
    assert result["annual"] == annual
    assert result["source_name"] == "ESPN (zonas) + FutbolArgentino.com (Anual)"
    assert result["warnings"] == []
    assert result["error"] is None
    assert result["save_snapshot"] is True


def test_cae_a_futbolargentino_si_espn_falla_y_lo_aclara():
    zones, annual = _bases()
    result = select_lpf_tables(
        espn_error="ESPN fuera de servicio",
        fa_zones=zones,
        fa_annual=annual,
    )

    assert result["source_name"] == "FutbolArgentino.com"
    assert result["warnings"] == [
        "ESPN rechazó las posiciones; se usó el respaldo automático."
    ]
    assert result["error"] is None


def test_con_zonas_frescas_reutiliza_solo_anual_del_snapshot():
    zones, annual = _bases()
    result = select_lpf_tables(
        espn_zones=zones,
        snapshot_zones=zones,
        snapshot_annual=annual,
        snapshot_source="foto de prueba",
        snapshot_age_hours=2.5,
    )

    assert result["zones"] == zones
    assert result["annual"] == annual
    assert result["source_name"] == "ESPN (zonas) + último respaldo (foto de prueba) (Anual)"
    assert result["warnings"] == [
        "La Tabla Anual no pudo actualizarse; uso la última válida de hace 2,5 horas."
    ]
    assert result["save_snapshot"] is False


def test_si_snapshot_anual_no_coincide_usa_primer_fallback_local_valido():
    zones, annual = _bases()
    bad_annual = deepcopy(annual)
    bad_annual.pop(next(iter(bad_annual)))
    result = select_lpf_tables(
        espn_zones=zones,
        snapshot_annual=bad_annual,
        snapshot_source="vieja",
        snapshot_age_hours=1,
        annual_fallbacks=[
            ("Tabla Anual de la sesión", annual),
            ("Tabla Anual incluida en la aplicación", annual),
        ],
    )

    assert result["annual"] == annual
    assert result["source_name"] == "ESPN (zonas) + Tabla Anual de la sesión (Anual)"
    assert result["warnings"] == [
        "La Tabla Anual no pudo actualizarse; uso tabla anual de la sesión."
    ]


def test_sin_fuentes_usa_snapshot_completo():
    zones, annual = _bases()
    result = select_lpf_tables(
        espn_error="ESPN caído",
        fa_zones_error="zonas caídas",
        fa_annual_error="anual caída",
        snapshot_zones=zones,
        snapshot_annual=annual,
        snapshot_source="ESPN + FA",
        snapshot_age_hours=7,
    )

    assert result["zones"] == zones
    assert result["annual"] == annual
    assert result["source_name"] == "Último respaldo válido · ESPN + FA"
    assert result["warnings"] == [
        "No pude consultar las fuentes ahora. Uso la última foto válida (ESPN + FA), guardada hace 7 horas."
    ]
    assert result["error"] is None


def test_sin_ningun_candidato_devuelve_error_con_diagnosticos():
    result = select_lpf_tables(
        espn_error="ESPN caído",
        fa_zones_error="zonas caídas",
        fa_annual_error="anual caída",
        snapshot_error="no existe respaldo",
    )

    assert result["zones"] == {}
    assert result["annual"] == {}
    assert result["warnings"] == []
    assert result["error"] == (
        "No pude obtener las zonas automáticamente. ESPN caído | "
        "FutbolArgentino.com (zonas): zonas caídas | "
        "FutbolArgentino.com (Anual): anual caída | "
        "Último respaldo: no existe respaldo"
    )


def test_modulo_no_depende_de_streamlit_ni_red():
    import lpf_table_selection

    source = open(lpf_table_selection.__file__, encoding="utf-8").read()
    assert "import streamlit" not in source
    assert "import requests" not in source
