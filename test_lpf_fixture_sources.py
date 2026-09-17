

def test_lpf_oficial_listing_descubre_cierres_y_notas_vivas_de_fecha():
    from lpf_fixture_sources import parse_lpf_official_listing_html

    html = """
    <html><body>
      <a href="/notas/primera/2026/08/15/agenda-de-la-fecha-6/">Racing y Boca empataron 1 a 1</a>
      <a href="/notas/primera/2026/08/15/agenda-de-la-fecha-6/">Leer más</a>
      <a href="/notas/primera/2026/09/10/se-mueve-la-novena/">Culminó la novena</a>
      <a href="/notas/primera/2026/09/07/hoy-arranca-la-fecha-8/">Adiós a la fecha 8</a>
      <a href="/notas/primera/2026/08/25/programacion-de-la-fecha-7-5/">Se fue la séptima</a>
      <a href="/notas/primera/2026/08/24/agenda-de-la-fecha-6/">Todo sobre la sexta</a>
      <a href="/notas/primera/2026/09/16/conferencia/">Conferencia del clásico rosarino</a>
      <a href="/notas/proyeccion/2026/08/15/resultados/">Proyección goleó</a>
      <a href="https://www.ligaprofesional.ar/notas/primera/2026/08/09/programacion-de-la-fecha-4-3/">Cerró la 4 en el Kempes</a>
    </body></html>
    """
    rows = parse_lpf_official_listing_html(
        html, base_url="https://www.ligaprofesional.ar/notas/primera/"
    )
    assert [row["title"] for row in rows] == [
        "Racing y Boca empataron 1 a 1",
        "Culminó la novena",
        "Adiós a la fecha 8",
        "Se fue la séptima",
        "Todo sobre la sexta",
        "Cerró la 4 en el Kempes",
    ]
    assert all("/notas/primera/2026/" in row["url"] for row in rows)


def test_lpf_oficial_listing_incluye_agendas_de_fecha_pero_no_conferencias():
    from lpf_fixture_sources import parse_lpf_official_listing_html

    html = """
    <a href="/notas/primera/2026/09/16/programacion-de-la-fecha-10/">Programación de la fecha 10</a>
    <a href="/notas/primera/2026/09/01/agenda-de-la-8-a-la-11/">Agenda de la 8 a la 11</a>
    <a href="/notas/primera/2026/09/05/conferencia-rosarina/">Conferencia del clásico rosarino</a>
    """
    rows = parse_lpf_official_listing_html(
        html, base_url="https://www.ligaprofesional.ar/notas/primera/"
    )
    assert [row["title"] for row in rows] == [
        "Programación de la fecha 10",
        "Agenda de la 8 a la 11",
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


def test_lpf_oficial_article_formato_real_fecha6_extrae_12_jugados_y_no_programados():
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
        "19.00 Tigre – Central Córdoba -TNT Sports-",
        "21.15 Lanús – Argentinos -TNT Sports-",
        "21.15 Talleres – Rosario Central -ESPN Premium-",
    ]
    html = "<article>" + "".join(f"<p>{line}</p>" for line in lines) + "</article>"
    rows = parse_lpf_official_results_article_html(
        html, canon_club=canon_club, official_fixture=LPF_FIXTURE
    )
    assert len(rows) == 12
    assert {row["round"] for row in rows} == {6}
    assert ("River Plate", "Vélez Sarsfield", 2, 2) in {
        (row["home"], row["away"], row["home_score"], row["away_score"])
        for row in rows
    }
