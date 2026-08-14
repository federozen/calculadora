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


def test_definition_radar_restores_full_editorial_report_before_visuals():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    assert "def _definition_editorial_report_text" in source
    helper = source[source.index("def _definition_editorial_report_text"):source.index("def render_definition_radar")]
    assert "_lpf_editorial_need_text" in helper
    shared = source[source.index("def _lpf_editorial_need_text"):source.index("def _lpf_objective_label")]
    assert "lpf_playoffs_texto" in shared
    assert "lpf_copas_necesita_texto" in shared
    assert "lpf_descenso_texto" in shared
    radar = source[source.index("def render_definition_radar"):source.index("def _scenario_window_games")]
    assert "Informe editorial del equipo" in radar
    assert "Lectura visual de la fecha" in radar
    assert "realidad de hoy, proyección del modelo, referencia histórica, peso del fixture" in radar
    assert radar.index("Informe editorial del equipo") < radar.index("Lectura visual de la fecha")
    assert radar.index("Informe editorial del equipo") < radar.index("Contexto automático · quiénes están alrededor")
    # El informe largo debe quedar visible: no detrás de un expander.
    report_slice = radar[radar.index('ui_markdown("### Informe editorial del equipo")'):radar.index('ui_markdown("## Lectura visual de la fecha")')]
    assert "st.expander" not in report_slice


def test_cup_visuals_restore_probability_heatmap_and_current_slot_map():
    from lpf_display import cup_current_slots_spec, cup_probability_heatmap_spec, probability_scale_color

    assert probability_scale_color(0) == "#b71c1c"
    assert probability_scale_color(50) == "#f9a825"
    assert probability_scale_color(100) == "#1b5e20"

    heat = cup_probability_heatmap_spec(
        [
            {
                "Equipo": "River Plate",
                "Anual": "8º",
                "Libertadores %": 35,
                "Sudamericana %": 40,
                "Al menos Sudamericana %": 75,
            }
        ],
        active_objective="Libertadores",
        focus_team="River Plate",
        simulations=6000,
    )
    assert heat["row_headers"] == ["★ River Plate · Anual 8º"]
    assert [cell[0] for cell in heat["cells"][0]] == ["35%", "40%", "75%"]
    assert "ESTIMADO" in heat["titulo"]
    assert "No es garantía matemática" in heat["footer"]

    slots = cup_current_slots_spec(
        {
            "A": {"pts": 20, "pj": 10},
            "B": {"pts": 18, "pj": 10},
            "C": {"pts": 15, "pj": 10},
            "D": {"pts": 13, "pj": 10},
        },
        ["A", "B", "C", "D"],
        ["B", "C", "D"],
        libertadores_slots=1,
    )
    states = [row[3][0] for row in slots["cells"]]
    assert states == [
        "LIBERTADORES · VÍA DIRECTA",
        "LIBERTADORES · TABLA ANUAL",
        "SUDAMERICANA · TABLA ANUAL",
        "SUDAMERICANA · TABLA ANUAL",
    ]
    assert "EXACTO" in slots["titulo"]
    assert "No es una proyección" in slots["footer"]


def test_libertadores_and_sudamericana_get_full_visual_dashboard():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    helper = source[source.index("def _render_cup_visual_dashboard"):source.index("def render_visualizations_workspace")]
    for label in (
        "tablero visual de la Tabla Anual",
        "Mapa de probabilidades de Copas",
        "escala rojo→amarillo→verde",
        "ESTIMADO · la otra cancha",
        "Calcular partidos que más ayudan o perjudican",
        "Cruces futuros entre competidores",
    ):
        assert label in helper
    assert "cup_current_slots_spec" in helper
    assert "cup_probability_heatmap_spec" in helper
    assert "placa_chances_mc_png" in helper
    assert "lpf_conviene_obj" in helper

    workspace = source[source.index("def render_visualizations_workspace"):source.index("def render_guided_workspace")]
    assert '_comp_view in ("Libertadores", "Sudamericana")' in workspace
    assert "_render_cup_visual_dashboard(E, team, _comp_view)" in workspace


def test_ultimas_fechas_copas_shows_heatmap_and_other_pitch_in_same_screen():
    source = Path("calculadora_futbol_argentino.py").read_text(encoding="utf-8")
    radar = source[source.index("def render_definition_radar"):source.index("def _scenario_window_games")]
    assert "Mapa de probabilidades de Copas · escala de color" in radar
    assert "cup_probability_heatmap_spec" in radar
    assert "radar_cup_probability_map_" in radar
    assert "lpf_conviene_obj" in radar
    assert "Cruces futuros entre competidores de Copas" in radar
    assert "Para copas, el impacto estimado de otras canchas se consulta" not in radar
