from pathlib import Path


def test_definition_radar_exposes_exact_conditionals_and_activation_window():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    assert "Qué tiene que pasar esta fecha · EXACTO" in source
    assert "Visualizaciones → Últimas fechas → Condicionales de un equipo" in source
    assert "A partir de 4 partidos restantes" in source
    assert "Frecuencia combinatoria, NO probabilidad" in source
    assert "next_round_conditionals(base, rest, juegos, team, 8" in source


def test_definition_radar_keeps_estimated_other_results_separate():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    assert "impacto Monte Carlo sigue separado como ESTIMADO" in source
    assert "ESTIMADO · diferencia entre el mejor y el peor desenlace" in source


def test_definition_radar_exposes_editorial_visual_suite_and_objectives():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    for label in (
        "Elegí qué querés analizar",
        "Elegí el equipo principal",
        "Contexto automático · quiénes están alrededor",
        "Qué pasa si gana, empata o pierde",
        "Semáforo compacto",
        "Otra cancha clave · doble entrada",
        "Árbol reducido del camino",
        "Reloj de definición",
        "¿Por qué? · explicar gana / empata / pierde",
        "¿Por qué? · explicar un equipo de la matriz",
    ):
        assert label in source
    assert "Libertadores por Tabla Anual" in source
    assert "Al menos Sudamericana por Tabla Anual" in source
    assert "st.multiselect" in source
    assert "default=[team_focus]" not in source
    assert "radar_matrix_comparators_" in source
    assert "— Elegí un equipo —" in source
    assert "Comparar también con… (opcional)" in source
    assert "no se agregan solas" in source
    assert "Equipo de la otra cancha (sugerido, editable)" in source
    assert "Filas = resultado de **{team_focus}**. Columnas = resultado de **{key_team}**" in source
    assert "No se elige al azar" in source


def test_definition_radar_separates_principal_context_comparators_and_key_match():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    assert "Equipo principal** = lo elegís vos" in source
    assert "Contexto automático** = clubes cercanos" in source
    assert "Comparadores** = únicamente los que vos agregás" in source
    assert "selected_teams = [team_focus] +" in source
    assert "comparator_options = [name for name in ordered if name != team_focus]" in source
    assert "No se selecciona ninguno automáticamente" in source
    assert "Estos equipos aparecen automáticamente porque están cerca del equipo principal o del corte" in source
    assert "No se muestran comparadores ni doble entrada porque este club ya no disputa este cupo" in source
    assert 'selection_ordered = list(liga_tabla_df(ctx["annual"])["Equipo"])' in source


def test_definition_radar_does_not_present_new_visuals_as_probability():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    assert "no usan probabilidades" in source
    assert "Los demás partidos de la fecha quedan abiertos y se enumeran exactamente" in source
