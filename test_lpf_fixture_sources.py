

def test_lpf_oficial_listing_descubre_resultados_y_hubs_de_fecha():
    from lpf_fixture_sources import parse_lpf_official_listing_html

    html = """
    <html><body>
      <a href="/notas/primera/2026/08/15/agenda-de-la-fecha-6/">Racing y Boca empataron 1 a 1</a>
      <a href="/notas/primera/2026/08/15/agenda-de-la-fecha-6/">Leer más</a>
      <a href="/notas/primera/2026/08/20/programacion-de-la-fecha-7/">Programación de la fecha 7</a>
      <a href="/notas/primera/2026/08/10/agenda-de-la-fecha-5-5/">Agenda de la fecha 5</a>
      <a href="/notas/primera/2026/08/07/agenda-de-la-fecha-4-a-la-7/">Agenda de la fecha 4 a la 7</a>
      <a href="/notas/proyeccion/2026/08/15/resultados/">Proyección goleó</a>
      <a href="https://www.ligaprofesional.ar/notas/primera/2026/08/09/programacion-de-la-fecha-4-3/">Cerró la 4 en el Kempes</a>
    </body></html>
    """
    rows = parse_lpf_official_listing_html(
        html, base_url="https://www.ligaprofesional.ar/notas/primera/"
    )
    assert [row["title"] for row in rows] == [
        "Racing y Boca empataron 1 a 1",
        "Programación de la fecha 7",
        "Agenda de la fecha 5",
        "Cerró la 4 en el Kempes",
    ]
    assert all("/notas/primera/2026/" in row["url"] for row in rows)


def test_lpf_oficial_listing_incluye_hub_aunque_el_titulo_siga_siendo_agenda():
    """Regresión real 25/8: el cuerpo puede estar actualizado antes que la portada."""
    from lpf_fixture_sources import parse_lpf_official_listing_html

    html = """
    <html><body>
      <a href="/notas/primera/2026/08/15/agenda-de-la-fecha-6/">Agenda de la fecha 6</a>
      <a href="/notas/primera/2026/08/15/agenda-de-la-fecha-6/">Leer más</a>
    </body></html>
    """
    rows = parse_lpf_official_listing_html(
        html, base_url="https://www.ligaprofesional.ar/notas/primera/"
    )
    assert [row["url"] for row in rows] == [
        "https://www.ligaprofesional.ar/notas/primera/2026/08/15/agenda-de-la-fecha-6/"
    ]


def test_lpf_oficial_article_parsea_ambos_formatos_y_descarta_programados():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    html = """
    <html><body><article>
      <p>Fecha 6 – Interzonal</p>
      <p>Aldosivi 1 – 3 Unión -TNT Sports-</p>
      <p>Estudiantes (Río Cuarto) 0 – San Lorenzo 0</p>
      <p>River 2 – Vélez 2</p>
      <p>Racing 1 – Boca 1</p>
      <p>19.00 Tigre – Central Córdoba -TNT Sports-</p>
      <p>La nota dice que Lanús le ganó a Argentinos, pero sin marcador estructurado.</p>
    </article></body></html>
    """
    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.ligaprofesional.ar/notas/primera/test/",
    )
    played = {
        (row["home"], row["away"]): (row["home_score"], row["away_score"])
        for row in rows
    }
    assert played[("Aldosivi", "Unión")] == (1, 3)
    assert played[("Estudiantes de Río Cuarto", "San Lorenzo")] == (0, 0)
    assert played[("River Plate", "Vélez Sarsfield")] == (2, 2)
    assert played[("Racing", "Boca Juniors")] == (1, 1)
    assert ("Tigre", "Central Córdoba") not in played
    assert all(row["source"] == "Liga Profesional de Fútbol" for row in rows)


def test_lpf_oficial_article_formato_real_fecha6_extrae_15_jugados_al_cerrar_fecha():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    lines = [
        "Aldosivi 1 – 3 Unión -TNT Sports-",
        "Estudiantes (Río Cuarto) 0 – San Lorenzo 0",
        "Gimnasia 2 – 3 Gimnasia (Mza.)",
        "Atlético Tucumán 0 – 0 Instituto",
        "Independiente 0 – Ind. Rivadavia Mza. 0",
        "Newell’s 2 – Banfield 1",
        "Huracán 0 – Deportivo Riestra 0",
        "Sarmiento 2 – Estudiantes 0",
        "Barracas Central 1 – Platense 2",
        "Belgrano 1 – Defensa y Justicia 2",
        "River 2 – Vélez 2",
        "Racing 1 – Boca 1",
        "Tigre 2 – Central Córdoba 1",
        "Lanús 1 – Argentinos 1",
        "Talleres 2 – Rosario Central 2",
    ]
    html = "<article>" + "".join(f"<p>{line}</p>" for line in lines) + "</article>"
    rows = parse_lpf_official_results_article_html(
        html, canon_club=canon_club, official_fixture=LPF_FIXTURE
    )
    assert len(rows) == 15
    assert {row["round"] for row in rows} == {6}
    assert ("River Plate", "Vélez Sarsfield", 2, 2) in {
        (row["home"], row["away"], row["home_score"], row["away_score"])
        for row in rows
    }
    assert ("Tigre", "Central Córdoba", 2, 1) in {
        (row["home"], row["away"], row["home_score"], row["away_score"])
        for row in rows
    }


def test_lpf_oficial_article_no_fabrica_partido_de_otra_fecha_desde_div_contenedor():
    """Regresión real 25/8: un wrapper de Fecha 4 no puede crear Central-Estudiantes RC de F16."""
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    friday = [
        "Rosario Central 2 – 1 Aldosivi (Zona B)",
        "Ind. Rivadavia Mza. 2 – 1 Estudiantes (Río Cuarto) (Zona B)",
    ]
    saturday = [
        "Deportivo Riestra 2 – 0 Estudiantes (Zona A)",
        "Atlético Tucumán 1 – 2 Sarmiento (Zona B)",
        "Tigre 1 – River 0 (Zona B)",
        "Boca 1 – Vélez 1, en el estadio Tomás A. Ducó (Zona A)",
        "Independiente 0 – Platense 1 (Zona A)",
        "Instituto 1 – Gimnasia (Mza.) 0 (Zona A)",
    ]
    sunday = [
        "San Lorenzo 0 – Huracán 2 (Interzonal)",
        "Defensa y Justicia 2 – Newell’s 1 (Zona A)",
        "Gimnasia 2 – Barracas Central 0 (Zona B)",
        "Argentinos 2 – Racing 1 (Zona B)",
    ]
    close = [
        "Banfield 0 – Belgrano 2 (Zona B)",
        "Unión 1 – Central Córdoba 2 (Zona A)",
        "Talleres 0 – Lanús 3 (Zona A)",
    ]
    groups = [friday, saturday, sunday, close]
    html = "<article><h2>Fecha 4</h2>" + "".join(
        '<div class="day">' + "".join(f"<p>{line}</p>" for line in group) + "</div>"
        for group in groups
    ) + "</article>"

    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url=(
            "https://www.ligaprofesional.ar/notas/primera/2026/08/09/"
            "programacion-de-la-fecha-4-3/"
        ),
    )

    assert len(rows) == 15
    assert {row["round"] for row in rows} == {4}
    assert not any(
        row["home"] == "Rosario Central" and row["away"] == "Estudiantes de Río Cuarto"
        for row in rows
    )


def test_lpf_oficial_article_div_hoja_con_spans_sigue_siendo_parseable():
    """Endurecer wrappers no debe romper una fila real armada con spans."""
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    html = """
    <main>
      <h2>Fecha 6</h2>
      <div class="score-row"><span>Lanús</span> <span>1 – 1</span> <span>Argentinos</span></div>
    </main>
    """
    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.ligaprofesional.ar/notas/primera/2026/08/15/agenda-de-la-fecha-6/",
    )
    assert [(r["home"], r["away"], r["home_score"], r["away_score"], r["round"]) for r in rows] == [
        ("Lanús", "Argentinos Juniors", 1, 1, 6)
    ]


def test_lpf_oficial_article_fecha6_descarta_falsos_cruces_de_otras_fechas_en_wrappers():
    """Un div de F6 no puede reciclar su primer marcador sobre un cruce real de F5/F12."""
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    html = """
    <article>
      <h2>Fecha 6 – Interzonal</h2>
      <div class="day">
        <p>Estudiantes (Río Cuarto) 0 – San Lorenzo 0</p>
        <p>Gimnasia 2 – 3 Gimnasia (Mza.)</p>
        <p>Atlético Tucumán 0 – 0 Instituto</p>
      </div>
      <div class="day">
        <p>Newell’s 2 – Banfield 1</p>
        <p>Huracán 0 – Deportivo Riestra 0</p>
      </div>
    </article>
    """
    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.ligaprofesional.ar/notas/primera/2026/08/15/agenda-de-la-fecha-6/",
    )
    assert len(rows) == 5
    assert {row["round"] for row in rows} == {6}
    assert not any(
        row["home"] == "Estudiantes de Río Cuarto" and row["away"] == "Atlético Tucumán"
        for row in rows
    )
    assert not any(
        row["home"] == "Newell's Old Boys" and row["away"] == "Deportivo Riestra"
        for row in rows
    )
