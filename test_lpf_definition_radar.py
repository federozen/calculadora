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
        "Configurá el tablero",
        "Equipo principal",
        "Comparadores de la matriz G/E/P",
        "Otra cancha para la doble entrada",
        "Resultado del análisis",
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
    assert "Partido de la otra cancha" in source
    assert "filas = resultado propio; columnas = resultado completo de la otra cancha" in source
    assert "No se elige al azar" in source
    assert "no hace falta elegir un segundo equipo" in source
    assert "Partidos que más definen" in source
    assert "Caminos exactos que cambian" in source
    assert "No es probabilidad" in source


def test_definition_radar_separates_principal_context_comparators_and_key_match():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    assert "Equipo principal** = lo elegís vos" in source
    assert "Contexto automático** = clubes cercanos" in source
    assert "Comparadores** = únicamente los que vos agregás" in source
    assert "La otra cancha se elige como partido completo" in source
    assert "selected_teams = [team_focus] +" in source
    assert "comparator_options = [name for name in ordered if (not team_selected or name != team_focus)]" in source
    assert "No se selecciona ninguno automáticamente" in source
    assert "Estos equipos aparecen automáticamente porque están cerca del equipo principal o del corte" in source
    assert "Los controles quedan visibles arriba, pero no se construye doble entrada porque este club ya no disputa este cupo" in source
    assert 'selection_ordered = list(liga_tabla_df(ctx["annual"])["Equipo"])' in source


def test_definition_radar_does_not_present_new_visuals_as_probability():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    assert "no usan probabilidades" in source
    assert "Los demás partidos de la fecha quedan abiertos y se enumeran exactamente" in source


def test_definition_radar_exposes_all_configuration_before_results():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    positions = [
        source.index("Configurá el tablero"),
        source.index("Equipo principal", source.index("Configurá el tablero")),
        source.index("Comparadores de la matriz G/E/P"),
        source.index("Otra cancha para la doble entrada"),
        source.index("Resultado del análisis"),
        source.index("Contexto automático · quiénes están alrededor"),
    ]
    assert positions == sorted(positions)
    assert "Esta opción queda visible desde el inicio" in source
    assert "disabled=True" in source
    assert "Elegir un equipo no abre una vista distinta ni termina el flujo" in source
    assert "recién debajo se mostrará el resultado" in source



def test_definition_radar_streamlit_widget_updates_use_callbacks():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    start = source.index('ui_markdown("**Comparadores de la matriz G/E/P**")')
    end = source.index('selected_teams = [team_focus] +', start)
    block = source[start:end]
    assert "on_click=_radar_add_suggested_comparators" in block
    assert "on_click=_radar_clear_comparators" in block
    assert "if add_col.button(" not in block
    assert "if clear_col.button(" not in block
    assert "st.rerun()" not in block
    # El bug de Streamlit Cloud era mutar el key del multiselect después de crearlo.
    after_widget = block[block.index('comparators = st.multiselect('):]
    assert 'st.session_state[matrix_state_key] = list(dict.fromkeys' not in after_widget
    assert 'st.session_state[matrix_state_key] = []' not in after_widget


def test_definition_radar_surfaces_mundial_visuals_instead_of_hiding_them():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    for label in (
        "Visuales tipo Mundial visibles en esta pantalla",
        "Mapa de puestos después de esta fecha · EXACTO",
        "Cara a cara · principal vs comparadores",
        "Versión visual del partido bisagra del Mundial",
        "ESTIMADO · visual de chances",
        "Calcular visual de chances",
    ):
        assert label in source
    assert "_definition_rank_map_spec" in source
    assert "_definition_compare_spec" in source
    assert 'st.bar_chart(decisive_chart.set_index("Partido")' in source
    assert "placa_chances_mc_png" in source
    assert 'with st.expander("Estimaciones separadas"' not in source


def test_definition_rank_map_is_exact_and_not_a_fake_probability():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    block = source[source.index("def _definition_rank_map_spec"):source.index("def _definition_compare_spec")]
    assert "scenario_rank_bounds" in block
    assert "mejor y peor puesto matemáticamente posible" in source
    assert "sin convertir conteos de marcadores en probabilidad" in source
