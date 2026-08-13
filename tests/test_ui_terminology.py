"""Regresiones editoriales de la interfaz y narrativas LPF."""
import ast
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

def test_accesos_principales_deja_puntos_por_objetivo_al_final():
    block = re.search(r"_WORKSPACES = \[(.*?)\]", MAIN, flags=re.DOTALL)
    assert block is not None
    labels = re.findall(r'"([^"\n]+)"', block.group(1))
    assert labels[-1] == "🎯 Puntos por objetivo"
    assert labels[0] == "🧭 Panel por equipo"



def test_chat_libre_se_integra_en_mesa_de_redaccion():
    block = re.search(r"_WORKSPACES = \[(.*?)\]", MAIN, flags=re.DOTALL)
    assert block is not None
    labels = re.findall(r'"([^"\n]+)"', block.group(1))
    assert "💬 Chat libre" not in labels
    assert "🗞️ Mesa de redacción" in labels
    assert '"Consultas y chat"' in MAIN
    assert "render_chat_workspace(E)" in MAIN
    assert 'st.session_state.get("workspace_nav") == "💬 Chat libre"' in MAIN
    assert 'st.session_state["workspace_nav"] = "🗞️ Mesa de redacción"' in MAIN
    assert 'key="newsroom_chat_sim_toggle"' in MAIN


def test_ultimas_fechas_muestra_tablero_y_condicionales():
    assert '"Últimas fechas"' in MAIN
    assert "Últimas fechas · tablero de definición" in MAIN
    assert "Puntos actuales y margen que queda" in MAIN
    assert "Si gana, empata o pierde" in MAIN
    assert "Abrir escalera exacta de puntos" in MAIN
    assert "Calcular qué resultados ajenos lo condicionan en la fecha" in MAIN
    assert "lpf_otros_resultados_sim(" in MAIN
    assert "lpf_previa_equipo_texto(" in MAIN


def test_monte_carlo_publicable_usa_6000_y_no_rotulos_viejos():
    assert "_LPF_PUBLIC_MC_RUNS = 6000" in MAIN
    assert "n=_LPF_PUBLIC_MC_RUNS" in MAIN
    assert "Estimación por simulación (6.000 torneos)" in MAIN
    assert "Calcular ahora (6.000 simulaciones)" in MAIN
    assert "4.000 torneos" not in MAIN
    assert "8.000 temporadas" not in MAIN


def test_playoffs_distingue_pj_partidos_por_jugar_y_puntos_totales():
    tree = ast.parse(MAIN)
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "lpf_playoffs_texto")
    segment = ast.get_source_segment(MAIN, fn) or ""
    assert "puntos totales en {pj} PJ" in segment
    assert "{gx} partidos por jugar" in segment
    assert 'L.append("### Partidos por jugar")' in segment
    assert 'L.append(f"- {rival}")' in segment
    assert "### Partidos pendientes" not in segment


def test_previa_por_equipo_expone_alcances_y_fecha_especifica():
    assert '"Alcance de la Previa"' in MAIN
    assert '["Próximo partido real", "Fecha oficial específica", "Fecha + postergados"]' in MAIN
    assert '"Fecha oficial específica": "official_round"' in MAIN
    assert '"Fecha + postergados": "extended_window"' in MAIN
    assert '"Fecha oficial para la Previa"' in MAIN
    assert "fecha=_preview_round" in MAIN
    assert "scope=_preview_scope" in MAIN


def test_probabilidades_playoffs_no_descartan_interzonales_reales():
    tree = ast.parse(MAIN)
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "liga_probabilidades_df")
    segment = ast.get_source_segment(MAIN, fn) or ""
    assert "if a in idx or b in idx" in segment
    assert "sa = float(s.get(a, 1.0))" in segment
    assert "sb = float(s.get(b, 1.0))" in segment
    assert "if a in idx and b in idx" not in segment
