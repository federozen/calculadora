"""Regresiones editoriales de la interfaz y narrativas LPF."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "calculadora_futbol_argentino.py").read_text(encoding="utf-8")
PISOS = (ROOT / "lpf_pisos.py").read_text(encoding="utf-8")
NARRATIVES = (ROOT / "lpf_competition_narratives.py").read_text(encoding="utf-8")
SCENARIOS = (ROOT / "lpf_scenarios.py").read_text(encoding="utf-8")


def test_interfaz_usa_tres_conceptos_editoriales_distintos():
    assert "🎯 Puntos por objetivo" in MAIN
    assert "Mínimo posible" in MAIN
    assert "Garantía exacta" in MAIN
    assert "Referencia conservadora" in MAIN
    assert "Puntaje que asegura" not in MAIN
    assert "Seguro (conservador)" not in MAIN
    assert "puntaje seguro (conservador)" not in MAIN.lower()
    assert "piso seguro" not in MAIN.lower()
    assert "piso ajustado" not in MAIN.lower()
    assert "Garantía matemática" not in SCENARIOS


def test_cota_no_aparece_en_interfaz_ni_narrativas_principales():
    for source in (MAIN, PISOS, NARRATIVES, SCENARIOS):
        assert re.search(r"\bcota\b", source, flags=re.IGNORECASE) is None


def test_ventana_exacta_no_vuelve_a_seis_fechas():
    assert "VENTANA_EXACTA = 8" in PISOS
    assert "if pend and gx <= VENTANA_EXACTA:" in MAIN
    assert "if pend and gx <= 6:" not in MAIN
    assert "remaining.get(team, 0))) <= VENTANA_EXACTA" in NARRATIVES
    assert "remaining.get(team, 0))) <= 6" not in NARRATIVES


def test_promedios_no_etiquetan_piso_techo_en_tabla_visible():
    assert '"Mínimo final": round(d["piso"], 3)' in MAIN
    assert '"Máximo final": round(d["techo"], 3)' in MAIN
    assert '"Piso": round(d["piso"], 3)' not in MAIN
