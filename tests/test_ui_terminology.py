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
    assert "Total seguro" in MAIN
    assert "Mínimo que asegura" in MAIN
    assert "Garantía exacta" not in MAIN
    assert "Referencia conservadora" not in MAIN
    assert "Puntaje que asegura" not in MAIN
    assert "Seguro (conservador)" not in MAIN
    assert "puntaje seguro (conservador)" not in MAIN.lower()
    assert "piso seguro" not in MAIN.lower()
    assert "piso ajustado" not in MAIN.lower()
    assert "Garantía matemática" not in SCENARIOS
    assert "Garantía exacta" not in SCENARIOS
    assert "Mínimo que asegura" in SCENARIOS
    assert "mínimo que garantiza" not in MAIN.lower()


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


def test_narrativa_explica_que_maximos_individuales_no_son_simultaneos():
    assert "Eso no significa que todos puedan hacerlo al mismo tiempo" in MAIN
    assert "máximos individuales son incompatibles entre sí" in MAIN
    assert "por eso no suma esos máximos individuales como si pudieran darse todos juntos" in MAIN


def test_total_seguro_explica_que_puede_no_ser_el_minimo():
    assert "Todavía no sabemos si" in MAIN
    assert "es el menor total que asegura" in MAIN
    assert "Puede que alcance con menos" in MAIN or "Puede alcanzar con menos" in MAIN


def test_escenarios_usa_nombre_claro_para_puntos_y_puesto_final():
    assert '"Puntos y puesto final"' in MAIN
    assert MAIN.count('"Puntaje y puesto"') == 1  # sólo migración de sesión vieja
    assert 'st.session_state.get("scenario_tool_nav") == "Puntaje y puesto"' in MAIN
    assert "¿Con cuántos puntos puede clasificar?" in MAIN
    assert "¿Con cuántos puntos suele terminar en un puesto específico?" in MAIN
    assert "¿Qué puesto querés analizar?" in MAIN


def test_busqueda_de_puesto_separa_estimacion_de_extremos_matematicos():
    assert "_sim_zone_rank_points" in MAIN
    assert "Mediana estimada" in MAIN
    assert "50% central" in MAIN
    assert "no es la mediana de los puntajes matemáticamente posibles" in MAIN
    assert "Mostrar también los extremos matemáticos (sin probabilidad)" in MAIN
    assert "can_finish_exact_rank_by_points" in MAIN
    assert "Esto no mide probabilidad" in MAIN
    assert "Mejor puesto con esos puntos" not in MAIN
    assert "Peor puesto con esos puntos" not in MAIN
    assert '"¿Puede ser ese puesto?": "Sí"' not in MAIN
